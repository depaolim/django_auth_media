import os

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from .models import MediaModel


class TestAcceptance(TestCase):

    def setUp(self):
        mm = MediaModel()
        name, content = "fname.xls", ContentFile("FILE-CONTENT")
        mm.slow_media.save(name, content)
        mm.xaccell_media.save(name, content)
        mm.secure_media.save(name, content)
        mm.save()
        self.u = User(username='N')
        self.u.set_password('P')
        self.u.save()
        self.client.login(username='N', password='P')
        url_pattern = os.path.join('/media/testapp/MediaModel/', str(mm.pk))
        self.expected_slow_url = os.path.join(url_pattern, "slow_media")
        self.expected_xaccell_url = os.path.join(url_pattern, "xaccell_media")
        self.expected_secure_url = os.path.join(url_pattern, "secure_media")
        self.mm = mm

    def test_url(self):
        self.assertEquals(self.mm.slow_media.url, self.expected_slow_url)
        self.assertEquals(self.mm.xaccell_media.url, self.expected_xaccell_url)
        self.assertEquals(self.mm.secure_media.url, self.expected_secure_url)

    def test_download_not_available(self):
        r = self.client.get(self.expected_slow_url)
        self.assertEquals(r.status_code, 404)
        r = self.client.get(self.expected_xaccell_url)
        self.assertEquals(r.status_code, 404)
        r = self.client.get(self.expected_secure_url)
        self.assertEquals(r.status_code, 404)

    def test_download_slow(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_slow_url)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.content, "FILE-CONTENT")

    def test_download_xaccell(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_xaccell_url)
        self.assertEquals(r.status_code, 200)
        self.assertFalse(r.content)
        expected_headers = [
            (
                r'X-Accel-Redirect:'
                ' /internal_media/xaccell/fname(_\w+)?.xls'),
            'X-Frame-Options: SAMEORIGIN',
            'Content-Type: application/vnd.ms-excel',
            r'Content-Disposition: attachment; filename=fname(_\w+)?.xls',
            'Vary: Cookie',
            ]
        self.assertRegexpMatches(
            r.serialize_headers(), "\r\n".join(expected_headers))

    def test_download_secure(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_secure_url)
        self.assertEquals(r.status_code, 302)
        self.assertFalse(r.content)
        self.assertRegexpMatches(
            r['Location'],
            (
                u'/protected/921ddd2a942e977cf646e892599ef099/'
                u'media_model_folder/fname(_\w+)?xls')
        )
