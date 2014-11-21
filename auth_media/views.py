import functools
import re

from django.conf import settings
from django.conf.urls import patterns, url
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_by_path

SERVERS = {}


for name, props in settings.MEDIA_SERVERS.items():
    engine_path = props.pop('ENGINE')
    kwargs = {name.lower(): value for name, value in props.items()}
    _do_serve = import_by_path(engine_path)
    SERVERS[name] = functools.partial(_do_serve, **kwargs)


def serve(
        request, app_label, object_name, object_pk, field_name,
        do_check_auth=lambda f, request: f.can_view(request),
        do_serve=None):
    model = models.loading.get_model(app_label, object_name)
    if not model:
        raise Http404
    instance = get_object_or_404(model, pk=object_pk)
    try:
        field_file = getattr(instance, field_name)
    except AttributeError:
        raise Http404
    if not do_check_auth(field_file, request):
        raise Http404
    if not do_serve:
        ms = field_file.field.media_server
        do_serve = SERVERS[ms if ms else "default"]
    return do_serve(request, field_file.name)


def urlpatterns(view=serve, **kwargs):
    prefix = re.escape(settings.MEDIA_URL.lstrip('/'))
    media_id = "/".join([
        r'(?P<app_label>[^/]+)',
        r'(?P<object_name>[^/]+)',
        r'(?P<object_pk>[^/]+)',
        r'(?P<field_name>[^/]+)', ])
    pattern = "^{}{}$". format(prefix, media_id)
    return patterns('', url(pattern, view, name='auth_media', kwargs=kwargs),)
