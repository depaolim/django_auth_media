import functools
import re

from django.conf import settings
from django.conf.urls import patterns, url
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_by_path

from .models import do_check_auth

SERVERS = {}


for name, props in settings.MEDIA_SERVERS.items():
    engine_path = props.pop('ENGINE')
    kwargs = {name.lower(): value for name, value in props.items()}
    _do_serve = import_by_path(engine_path)
    SERVERS[name] = functools.partial(_do_serve, **kwargs)


do_serve = SERVERS["xaccell"]


def serve(
        request, app_label, object_name, object_pk, field_name,
        do_check_auth=do_check_auth, do_serve=do_serve):
    model = models.loading.get_model(app_label, object_name)
    instance = get_object_or_404(model, pk=object_pk)
    field = getattr(instance, field_name)
    path = do_check_auth(request, instance, field_name)
    if not path:
        raise Http404
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
