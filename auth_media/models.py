# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import functools

from django.db import models
from django.conf import settings

try:
    from django.utils.module_loading import import_string
except ImportError:
    # Django 1.6.11
    from django.utils.module_loading import import_by_path
    import_string = import_by_path


class AuthFieldFile(models.fields.files.FieldFile):

    MEDIA_ID = "/".join([
        r'(?P<app_label>[^/]+)',
        r'(?P<object_name>[^/]+)',
        r'(?P<object_pk>[^/]+)',
        r'(?P<field_name>[^/]+)', ])

    def _url(self):
        s, i, f = self.storage, self.instance, self.field
        m = i._meta
        return s.url("/".join([m.app_label, m.object_name, str(i.pk), f.name]))
    url = property(_url)

    def can_view(self, request):
        if request.user.is_superuser:
            return True
        p = self.field.permission
        if not p:
            return False
        if callable(p):
            return p(self.instance, request)
        return request.user.has_perm(p)

    def get_view(self):
        ms = getattr(self.field, "media_server", None)
        servers = {}
        for name, props in settings.MEDIA_SERVERS.items():
            props = dict(props)
            engine_path = props.pop('ENGINE')
            kwargs = {name.lower(): value for name, value in props.items()}
            _do_serve = import_string(engine_path)
            servers[name] = functools.partial(_do_serve, **kwargs)

        view = servers[ms if ms else "default"]
        return lambda request: view(request, self.name)


class AuthFileField(models.FileField):

    attr_class = AuthFieldFile

    def __init__(self, *args, **kwargs):
        self.media_server = kwargs.pop("media_server", None)
        self.permission = kwargs.pop("permission", None)
        super(AuthFileField, self).__init__(*args, **kwargs)
