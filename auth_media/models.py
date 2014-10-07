import mimetypes
import os
import re

from django.conf import settings
from django.db import models
from django.conf.urls import patterns, url
from django.http import HttpResponse, HttpResponseNotFound


def do_check_auth(request, app_label, object_name, instance_pk, field_name):
    model = models.loading.get_model(app_label, object_name)
    instance = model.objects.get(pk=instance_pk)
    field = getattr(instance, field_name)
    if not request.user.is_superuser:
        try:
            can_view = getattr(model, "can_view_" + field_name)
        except AttributeError:
            return
        if not can_view(instance, request):
            return
    return field.name


def do_serve(request, path, media_root=None, media_redirect=None):
    if not media_root:
        media_root = settings.MEDIA_ROOT
    if not media_redirect:
        media_redirect=settings.MEDIA_REDIRECT
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


class AuthFieldFile(models.fields.files.FieldFile):

    def _url(self):
        s, i, f = self.storage, self.instance, self.field
        m = i._meta
        return s.url("/".join([m.app_label, m.object_name, str(i.pk), f.name]))
    url = property(_url)


class AuthFileField(models.FileField):

    attr_class = AuthFieldFile


def urlpatterns(view=serve, **kwargs):
    prefix = re.escape(settings.MEDIA_URL.lstrip('/'))
    media_id = "/".join([
        r'(?P<app_label>[^/]+)',
        r'(?P<object_name>[^/]+)',
        r'(?P<object_pk>[^/]+)',
        r'(?P<field_name>[^/]+)',])
    pattern = "^{}{}$". format(prefix, media_id)
    return patterns('', url(pattern, view, name='auth_media', kwargs=kwargs),)
