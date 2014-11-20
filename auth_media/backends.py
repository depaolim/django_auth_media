import mimetypes
import os

from django.conf import settings
from django.http import HttpResponse


def interim():
    pass


def xaccell(request, path, media_root=None, media_redirect=None):
    if not media_root:
        media_root = settings.MEDIA_ROOT
    if not media_redirect:
        media_redirect = settings.MEDIA_REDIRECT
    fpath = os.path.join(media_root, path)
    bname = os.path.basename(path)
    content_type, encoding = mimetypes.guess_type(fpath)
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = "attachment; filename={}".format(bname)
    response['X-Accel-Redirect'] = os.path.join(media_redirect, path)
    return response


def secure_link():
    pass
