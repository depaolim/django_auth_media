import StringIO
import zipfile

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.urlresolvers import resolve, reverse
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse
from django.test import TestCase

from .backends import interim, secure_link, xaccel
from .models import AuthFileField
from .views import serve, urlpatterns


def can_view_dummy_f_a(dummy, request):
    return dummy.guard


class Dummy(models.Model):
    f_a = AuthFileField(upload_to="xxx", permission=can_view_dummy_f_a)
    f_b = AuthFileField(
        upload_to="xxx", permission=u'auth_media.view_file_b')
    f_c = AuthFileField(upload_to="xxx")
    guard = models.BooleanField(default=False)

    class Meta:
        permissions = (
            ("view_file_b", "Can view file"),
        )


class TestBackends(TestCase):

    def setUp(self):
        stream = StringIO.StringIO()
        with zipfile.ZipFile(stream, "w") as zf:
            zf.writestr("sample.csv", "csv,file,content")
        self.media_name = default_storage.save(
            "my_folder/my_name.zip",
            ContentFile(stream.getvalue()))

    def tearDown(self):
        default_storage.delete(self.media_name)

    def test_interim(self):
        req = HttpRequest()
        r = interim(req, self.media_name)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(b''.join(r.streaming_content)[0:2], b'PK')

    def test_secure_link(self):
        req = HttpRequest()
        r = secure_link(
            req, self.media_name,
            secret="SuP3rS3cr3t", redirect="media_secure")
        self.assertEquals(r.status_code, 302)
        expected_headers = [
            "Content-Type: text/html; charset=utf-8",
            (
                "Location: "
                "media_secure/1f4cf3b8507c40387c8e95a6d5ea1cc6/"
                "my_folder/my_name.zip"),
            ]
        self.assertEquals(r.serialize_headers(), "\r\n".join(expected_headers))

    def test_xaccel(self):
        req = HttpRequest()
        r = xaccel(
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
            Http404, serve,
            "dummy_req", "auth_media", "Wrong", self.dm.pk + 1, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_404_on_invalid_instance(self):
        self.assertRaises(
            Http404, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk + 1, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_internal_error_on_invalid_field_name(self):
        self.assertRaises(
            Http404, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "dummy_field",
            do_check_auth=None, do_serve=None)

    def test_on_not_authorized(self):
        self.assertRaises(
            Http404, serve,
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "f_a",
            do_check_auth=lambda *args: self._dummy_method(False, *args),
            do_serve=None)
        self._assertCall(self.dm.f_a, "dummy_req")
        self._assertNoMoreCalls()

    def test_on_authorized_with_content(self):
        self.dm.f_a.save("SAMPLE_P", ContentFile("CONTENT-P"))
        response = serve(
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "f_a",
            do_check_auth=lambda *args: self._dummy_method(True, *args),
            do_serve=lambda *args: self._dummy_method(HttpResponse(), *args)
            )
        self._assertCall(self.dm.f_a, "dummy_req")
        req, path = self._calls.pop(0)
        self.assertEquals(req, "dummy_req")
        self.assertRegexpMatches(path, "^xxx/SAMPLE_P")
        self._assertNoMoreCalls()
        self.assertEquals(response.status_code, 200)

    def test_on_authorized_without_content(self):
        response = serve(
            "dummy_req", "auth_media", "Dummy", self.dm.pk, "f_a",
            do_check_auth=lambda *args: self._dummy_method(True, *args),
            do_serve=lambda *args: self._dummy_method(HttpResponse(), *args)
            )
        self._assertCall(self.dm.f_a, "dummy_req")
        self._assertCall("dummy_req", "")
        self._assertNoMoreCalls()
        self.assertEquals(response.status_code, 200)


class TestAuthFileFieldUrl(TestCase):

    def setUp(self):
        self.da = Dummy()
        self.da.save()

    def test_url(self):
        self.da.f_a.save("NAME", ContentFile("CONTENT"))
        self.assertEquals(
            self.da.f_a.url,
            "/media/auth_media/Dummy/{}/f_a".format(self.da.pk))


class TestAuthFileFieldCanView(TestCase):

    def setUp(self):
        self.u = User()
        self.u.save()
        self.req = HttpRequest()
        self.req.user = self.u
        self.da = Dummy()
        self.da.save()

    def test_on_guard_and_not_found(self):
        self.assertFalse(self.da.f_a.can_view(self.req))

    def test_on_guard_and_serve(self):
        self.da.f_a.save("NAME-A", ContentFile("CONTENT-A"))
        self.da.guard = True
        self.da.save()
        self.assertTrue(self.da.f_a.can_view(self.req))

    def test_on_perm_and_not_found(self):
        self.assertFalse(self.da.f_a.can_view(self.req))

    def test_on_perm_and_serve(self):
        self.da.f_b.save("NAME-B", ContentFile("CONTENT-B"))
        self.u.user_permissions.add(
            Permission.objects.get(codename="view_file_b"))
        self.u.save()
        self.assertTrue(self.da.f_b.can_view(self.req))

    def test_on_nothing_and_not_found(self):
        self.assertFalse(self.da.f_a.can_view(self.req))

    def test_on_nothing_and_serve(self):
        self.da.f_c.save("NAME-C", ContentFile("CONTENT-C"))
        self.u.is_superuser = True
        self.u.save()
        self.assertTrue(self.da.f_a.can_view(self.req))


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
        self.assertRegexpMatches(dummy_do_serve_calls.pop(), "^xxx/NAME_")
        self.assertEquals(response.status_code, 200)
