from django.db import models


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


class AuthFileField(models.FileField):

    attr_class = AuthFieldFile

    def __init__(self, *args, **kwargs):
        self.media_server = kwargs.pop("media_server", None)
        self.permission = kwargs.pop("permission", None)
        super(AuthFileField, self).__init__(*args, **kwargs)
