from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context.get('response').status_code
        if status.is_success(status_code):
            response_data = {'code': 200, 'data': data if data else []}
            if isinstance(data, dict):
                response_data = {'code': 200, 'data': data}
                if data.get('error'):
                    response_data = {'code': 200, 'error': data.get('error'), 'data': {}}
        else:
            response_data = {'code': 50000, 'data': [], 'errors': data}
        # call super to render the response
        response = super(CustomJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)
        return response


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response


class CustomModelMixin(object):
    def destroy(self, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        super().destroy(*args, **kwargs)
        return Response(serializer.data, status=status.HTTP_200_OK)


def get_opinion(section_score, section_opinion_list):
    res = ""
    for section_opinion_index, section_opinion in enumerate(section_opinion_list):
        title = section_opinion.get('title')
        if section_score >= 95:
            grade = section_opinion.get('grade1')
        elif 95 <= section_score >= 80:
            grade = section_opinion.get('grade2')
        elif 80 <= section_score >= 70:
            grade = section_opinion.get('grade3')
        else:
            grade = section_opinion.get('grade4')
        res += title.replace('*', grade) + '\n'
    return res


def get_score(data_list):
    total_score = 0
    content_score_list = []
    for content in data_list:
        content_weights = int(content.get('weights'))
        section_list = content.get('section_list')
        content_scoring = 0
        section_total_score = 0
        for section in section_list:
            section_score = int(section.get('score'))
            section_total_score += section_score
            for item in section.get('item_list'):
                content_scoring += int(item.get('scoring'))
        content_scoring = round((content_scoring / section_total_score * 100) * (content_weights / 100))
        total_score += content_scoring
        content_score_list.append({
            'title': content.get('title'),
            'score': content_scoring
        })
    return total_score, content_score_list


def get_result_data(result):
    table_data = []
    content_score_list = []
    score = {}
    opinion = {}

    for result_index, result_value in enumerate(result):
        index = result_index + 1
        section_total_score_list = []
        section_total_points_list = []
        section_opinion = ""

        for section_index, section_value in enumerate(result_value.get('section_list')):
            subentry_score_list = []
            item_name = f"{section_index + 1}.{section_value.get('title')}"

            section_data = dict()
            section_data['id'] = index
            section_data['content'] = result_value.get('title')
            section_data['item'] = item_name
            section_data['opinion'] = ''

            for item in section_value.get('item_list'):
                subentry_score_list.append(int(item.get('scoring')) if item.get('scoring').isdigit() else 0)

            section_score = round(sum(subentry_score_list) / int(section_value.get('score')) * 100)
            section_opinion += get_opinion(section_score, section_value.get('opinion_list'))
            section_data['score'] = section_score
            section_data['score_list'] = subentry_score_list
            table_data.append(section_data)
            section_total_score_list.append(int(section_value.get('score')))
            section_total_points_list.append(sum(subentry_score_list))
        score[result_value.get('title')] = {
            'weight': int(result_value.get('weights')),
            'section_total_points': sum(section_total_points_list),
            'section_total_score': sum(section_total_score_list),
            'opinion_list': result_value.get('opinion_list')
        }
        opinion[result_value.get('title')] = section_opinion
    table_total_score_list = []

    for k, v in score.items():
        for i in table_data:
            if i.get('content') == k:
                i['compute_weights_score'] = round(v.get('section_total_points') * (v.get('weight') / 100))
                i['opinion'] = opinion.get(i.get('content'))
                i['totalScore'] = round(v.get('section_total_points') / v.get('section_total_score') * 100)
                if not v.get('total_score'):
                    score[k]['total_score'] = round(v.get('section_total_points') * v.get('weight') / 100)
    overall_opinion = [y for x in [i.get('opinion_list') for i in score.values()] for y in x]
    overall_evaluation_list = []
    special_evaluation_list = []

    for i in score:
        section_total_points = score.get(i).get('section_total_points')
        content_score_list.append({
            'title': i,
            'score': round(score.get(i).get('section_total_points') * (score.get(i).get('weight') / 100))
        })
        special_evaluation = {
            "id": 6,
            "content": "特别评价",
            "item": i,
            "opinion": '',
            "totalScore": section_total_points
        }
        overall_evaluation = {
            "id": 7,
            "content": "整体评价",
            "item": i,
            "opinion": get_opinion(section_total_points, overall_opinion),
            "totalScore": section_total_points
        }
        overall_evaluation_list.append(overall_evaluation)
        special_evaluation_list.append(special_evaluation)
        # table_data.append(evaluation)
        table_total_score_list.append(score.get(i).get('total_score'))
    table_data += special_evaluation_list
    table_data += overall_evaluation_list

    return table_data, sum(table_total_score_list), content_score_list
