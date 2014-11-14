import mimetypes
import os
import re

from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponse, HttpResponseNotFound

from .models import do_check_auth


def do_serve(request, path, media_root=None, media_redirect=None):
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


def serve(
        request, app_label, object_name, object_pk, field_name,
        do_check_auth=do_check_auth, do_serve=do_serve):
    path = do_check_auth(request, app_label, object_name, object_pk, field_name)
    if not path:
        return HttpResponseNotFound()
    return do_serve(request, path)


def urlpatterns(view=serve, **kwargs):
    prefix = re.escape(settings.MEDIA_URL.lstrip('/'))
    media_id = "/".join([
        r'(?P<app_label>[^/]+)',
        r'(?P<object_name>[^/]+)',
        r'(?P<object_pk>[^/]+)',
        r'(?P<field_name>[^/]+)', ])
    pattern = "^{}{}$". format(prefix, media_id)
    return patterns('', url(pattern, view, name='auth_media', kwargs=kwargs),)
