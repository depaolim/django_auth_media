# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import hashlib
import mimetypes
import os

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.static import serve


def interim(request, path):
    return serve(request, path, settings.MEDIA_ROOT)


def xaccel(request, path, root=None, redirect=None):
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
    m = hashlib.md5()
    m.update(path.encode("utf8"))
    m.update(secret.encode("utf8"))
    response = HttpResponseRedirect(os.path.join(redirect, m.hexdigest(), path))
    return response
