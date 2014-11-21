import StringIO
import zipfile

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import resolve, reverse
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse
from django.test import TestCase

from .models import do_check_auth, AuthFileField
from .views import serve, urlpatterns
from .backends import xaccell


class Dummy(models.Model):
    f_a = AuthFileField(upload_to="xxx")
    f_b = AuthFileField(upload_to="xxx")
    f_c = AuthFileField(upload_to="xxx")
    guard = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ("view_file_b", "Can view file"),
        )

    def can_view_f_a(self, request):
        return self.guard

    def can_view_f_b(self, request):
        return request.user.has_perm(u'auth_media.view_file_b')


class TestDoCheckAuth(TestCase):

    def setUp(self):
        self.u = User()
        self.u.save()
        self.req = HttpRequest()
        self.req.user = self.u
        self.da = Dummy()
        self.da.save()

    def test_on_guard_and_not_found(self):
        self.assertFalse(do_check_auth(self.req, self.da, "f_a"))

    def test_on_guard_and_serve(self):
        self.da.f_a.save("NAME-A", ContentFile("CONTENT-A"))
        self.da.guard = True
        self.da.save()
        self.assertRegexpMatches(
            do_check_auth(self.req, self.da, "f_a"),
            "xxx/NAME-A_?\d*")

    def test_on_perm_and_not_found(self):
        self.assertFalse(do_check_auth(self.req, self.da, "f_b"))

    def test_on_perm_and_serve(self):
        self.da.f_b.save("NAME-B", ContentFile("CONTENT-B"))
        self.u.user_permissions.add(
            Permission.objects.get(codename="view_file_b"))
        self.u.save()
        self.assertRegexpMatches(
            do_check_auth(self.req, self.da, "f_b"),
            "xxx/NAME-B_?\d*")

    def test_on_nothing_and_not_found(self):
        self.assertFalse(do_check_auth(self.req, self.da, "f_c"))

    def test_on_nothing_and_serve(self):
        self.da.f_c.save("NAME-C", ContentFile("CONTENT-C"))
        self.u.is_superuser = True
        self.u.save()
        self.assertRegexpMatches(
            do_check_auth(self.req, self.da, "f_c"),
            "xxx/NAME-C_?\d*")


class TestXAccell(TestCase):

    def setUp(self):
        stream = StringIO.StringIO()
        with zipfile.ZipFile(stream, "w") as zf:
            zf.writestr("sample.csv", "csv,file,content")
        self.fsf = FileSystemStorage()
        self.media_name = self.fsf.save(
            "my_folder/my_name.zip",
            ContentFile(stream.getvalue()))

    def tearDown(self):
        self.fsf.delete(self.media_name)

    def test_valid_path(self):
        req = HttpRequest()
        r = xaccell(
            req, self.media_name, root=settings.MEDIA_ROOT, redirect="redir")
        self.assertEquals(r.status_code, 200)
        expected_headers = [
            "X-Accel-Redirect: redir/my_folder/my_name.zip",
            "Content-Type: application/zip",
            "Content-Disposition: attachment; filename=my_name.zip"
            ]
        self.assertEquals(r.serialize_headers(), "\r\n".join(expected_headers))


class TestServe(TestCase):

    def setUp(self):
        self._calls = []
        self.dm = Dummy()
        self.dm.save()

    def _dummy_method(self, result, *args):
        self._calls.append(args)
        return result

    def _assertCall(self, *args):
        self.assertEquals(self._calls.pop(0), args)

    def _assertNoMoreCalls(self):
        self.assertFalse(self._calls)

    def test_internal_error_on_invalid_model(self):
        self.assertRaises(
            ValueError, serve,
            "dummy_req", "auth_media", "Wrong", self.dm.pk + 1, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_404_on_invalid_instance(self):
        self.assertRaises(
            Http404, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk + 1, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_internal_error_on_invalid_field_name(self):
        self.assertRaises(
            AttributeError, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_on_not_authorized(self):
        self.assertRaises(
            Http404, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "f_a",
            do_check_auth=lambda *args: self._dummy_method(None, *args),
            do_serve=None)
        self._assertCall("dummy_req", self.dm, "f_a")
        self._assertNoMoreCalls()

    def test_on_authorized(self):
        response = serve(
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "f_a",
            do_check_auth=lambda *args: self._dummy_method("SAMPLE_P", *args),
            do_serve=lambda *args: self._dummy_method(HttpResponse(), *args)
            )
        self._assertCall("dummy_req", self.dm, "f_a")
        self._assertCall("dummy_req", "SAMPLE_P")
        self._assertNoMoreCalls()
        self.assertEquals(response.status_code, 200)


class TestAuthFileField(TestCase):

    def setUp(self):
        self.da = Dummy()
        self.da.save()

    def test_url(self):
        self.da.f_a.save("NAME", ContentFile("CONTENT"))
        self.assertEquals(
            self.da.f_a.url,
            "/media/auth_media/Dummy/{}/f_a".format(self.da.pk))


class TestPatterns(TestCase):
    urls = urlpatterns()

    def test_reverse(self):
        url = reverse('auth_media', kwargs={
            'app_label': 'auth_media', 'object_name': 'Dummy',
            'object_pk': '1', 'field_name': 'f_a'}
        )
        self.assertEquals(url, "/media/auth_media/Dummy/1/f_a")

    def test_resolve(self):
        resolver = resolve("/media/auth_media/Dummy/1/f_a")
        self.assertEquals(resolver.kwargs, {
            'object_name': 'Dummy', 'field_name': 'f_a',
            'object_pk': '1', 'app_label': 'auth_media'}
        )
        self.assertEqual(resolver.func.func_name, 'serve')


class TestAcceptance(TestCase):

    def setUp(self):
        self.u = User()
        self.u.save()
        self.req = HttpRequest()
        self.req.user = self.u
        self.da = Dummy()
        self.da.save()

    def test_not_authorized(self):
        dummy_do_serve_calls = []

        def dummy_do_serve(req, path):
            dummy_do_serve_calls.append(path)
            return HttpResponse()

        self.da.f_a.save("NAME", ContentFile("CONTENT"))
        self.da.guard = False
        self.da.save()
        self.assertRaises(
            Http404, serve,
            self.req, "auth_media", "Dummy", self.da.pk, "f_a",
            do_serve=dummy_do_serve)
        self.assertFalse(dummy_do_serve_calls)

    def test_authorized(self):
        dummy_do_serve_calls = []

        def dummy_do_serve(req, path):
            dummy_do_serve_calls.append(path)
            return HttpResponse()

        self.da.f_a.save("NAME", ContentFile("CONTENT"))
        self.da.guard = True
        self.da.save()
        response = serve(
            self.req, "auth_media", "Dummy", self.da.pk, "f_a",
            do_serve=dummy_do_serve)
        self.assertRegexpMatches(dummy_do_serve_calls.pop(), "xxx/NAME_?\d*")
        self.assertEquals(response.status_code, 200)
