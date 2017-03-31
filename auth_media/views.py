# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import functools
import re

from django.conf import settings
from django.conf.urls import url
from django.http import Http404
from django.shortcuts import get_object_or_404

try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    # Django 1.6.11
    from django.db.models.loading import get_model

try:
    from django.utils.module_loading import import_string
except ImportError:
    # Django 1.6.11
    from django.utils.module_loading import import_by_path
    import_string = import_by_path

from .models import AuthFieldFile

SERVERS = {}


for name, props in settings.MEDIA_SERVERS.items():
    engine_path = props.pop('ENGINE')
    kwargs = {name.lower(): value for name, value in props.items()}
    _do_serve = import_string(engine_path)
    SERVERS[name] = functools.partial(_do_serve, **kwargs)


def serve(
        request, app_label, object_name, object_pk, field_name,
        do_check_auth=lambda f, request: f.can_view(request),
        do_serve=None):
    try:
        model = get_model(app_label, object_name)
        if not model:  # Django 1.6.11
            raise Http404
    except LookupError:
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
    pattern = "^{}{}$". format(
        re.escape(settings.MEDIA_URL.lstrip('/')),
        AuthFieldFile.MEDIA_ID)
    return [url(pattern, view, name='auth_media', kwargs=kwargs),]
