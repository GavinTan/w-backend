from datetime import datetime
from django.conf import settings
import os


def cleanup_file(path, day=7):
    """ 清理上传的过期文件 """

    now_time = datetime.now()
    for file in os.listdir(path):
        full_path = os.path.join(path, file)

        if (now_time - datetime.fromtimestamp(os.stat(full_path).st_mtime)).days > day:
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                cleanup_file(full_path)


cleanup_file(settings.UPLOAD_PATH)
