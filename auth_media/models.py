from django.db import models


def do_check_auth(request, instance, field_name):
    field = getattr(instance, field_name)
    if not request.user.is_superuser:
        try:
            can_view = getattr(instance, "can_view_" + field_name)
        except AttributeError:
            return
        if not can_view(request):
            return
    return field.name


class AuthFieldFile(models.fields.files.FieldFile):

    def _url(self):
        s, i, f = self.storage, self.instance, self.field
        m = i._meta
        return s.url("/".join([m.app_label, m.object_name, str(i.pk), f.name]))
    url = property(_url)


class AuthFileField(models.FileField):

    attr_class = AuthFieldFile

    def __init__(self, *args, **kwargs):
        self.media_server = kwargs.pop("media_server", None)
        super(AuthFileField, self).__init__(*args, **kwargs)
