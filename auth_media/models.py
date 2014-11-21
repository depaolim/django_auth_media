from django.db import models


class AuthFieldFile(models.fields.files.FieldFile):

    def _url(self):
        s, i, f = self.storage, self.instance, self.field
        m = i._meta
        return s.url("/".join([m.app_label, m.object_name, str(i.pk), f.name]))
    url = property(_url)

    def can_view(self, request):
        if request.user.is_superuser:
            return True
        try:
            f_can_view = getattr(self.instance, "can_view_" + self.field.name)
        except AttributeError:
            return False
        return f_can_view(request)


class AuthFileField(models.FileField):

    attr_class = AuthFieldFile

    def __init__(self, *args, **kwargs):
        self.media_server = kwargs.pop("media_server", None)
        super(AuthFileField, self).__init__(*args, **kwargs)
