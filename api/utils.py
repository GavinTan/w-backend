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
