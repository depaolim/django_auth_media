import mimetypes
import os

from django.conf import settings
from django.http import HttpResponse


def interim(request, path):
    pass


def xaccell(request, path, root=None, redirect=None):
    if not root:
        root = settings.MEDIA_ROOT
    fpath = os.path.join(root, path)
    bname = os.path.basename(path)
    content_type, encoding = mimetypes.guess_type(fpath)
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = "attachment; filename={}".format(bname)
    response['X-Accel-Redirect'] = os.path.join(redirect, path)
    return response


def secure_link(request, path):
    pass
