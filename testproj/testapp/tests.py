import os

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase

from .models import MediaModel


class TestAcceptance(TestCase):

    def setUp(self):
        mm = MediaModel()
        name, content = "fname.xls", ContentFile("FILE-CONTENT")
        mm.interim_media.save(name, content)
        mm.xaccel_media.save(name, content)
        mm.secure_media.save(name, content)
        mm.save()
        self.u = User(username='N')
        self.u.set_password('P')
        self.u.save()
        self.client.login(username='N', password='P')
        url_pattern = os.path.join('/media/testapp/MediaModel/', str(mm.pk))
        self.expected_interim_url = os.path.join(url_pattern, "interim_media")
        self.expected_xaccel_url = os.path.join(url_pattern, "xaccel_media")
        self.expected_secure_url = os.path.join(url_pattern, "secure_media")
        self.mm = mm

    def tearDown(self):
        default_storage.delete(self.mm.interim_media.name)
        default_storage.delete(self.mm.xaccel_media.name)
        default_storage.delete(self.mm.secure_media.name)

    def test_url(self):
        self.assertEquals(self.mm.interim_media.url, self.expected_interim_url)
        self.assertEquals(self.mm.xaccel_media.url, self.expected_xaccel_url)
        self.assertEquals(self.mm.secure_media.url, self.expected_secure_url)

    def test_download_not_available(self):
        r = self.client.get(self.expected_interim_url)
        self.assertEquals(r.status_code, 404)
        r = self.client.get(self.expected_xaccel_url)
        self.assertEquals(r.status_code, 404)
        r = self.client.get(self.expected_secure_url)
        self.assertEquals(r.status_code, 404)

    def test_download_interim(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_interim_url)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(b''.join(r.streaming_content), b"FILE-CONTENT")

    def test_download_xaccel(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_xaccel_url)
        self.assertEquals(r.status_code, 200)
        self.assertFalse(r.content)
        self.assertRegexpMatches(r['Content-Disposition'], r'attachment; filename=fname(_\w+)?.xls')
        self.assertRegexpMatches(r['Content-Type'], r'application/vnd.ms-excel')
        self.assertRegexpMatches(r['Content-Length'], '0')  # only in django 1.11.6
        self.assertRegexpMatches(r['X-Accel-Redirect'], '/internal_media/xaccel/fname(_\w+)?.xls')

    def test_download_secure(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_secure_url)
        self.assertEquals(r.status_code, 302)
        self.assertFalse(r.content)
        self.assertRegexpMatches(
            r['Location'],
            (
                u'/secure_media/42f5aacdc3f3ad9005ad7dc795ce877e/'
                u'secure/fname(_\w+)?.xls')
        )
