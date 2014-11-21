import hashlib
import mimetypes
import os

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.static import serve


def interim(request, path):
    return serve(request, path, settings.MEDIA_ROOT)


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


def secure_link(request, path, secret, redirect):
    hash = hashlib.md5("{}{}".format(path, secret)).hexdigest()
    response = HttpResponseRedirect(os.path.join(redirect, hash, path))
    return response
