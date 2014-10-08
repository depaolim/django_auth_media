from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from .models import *


class TestAcceptance(TestCase):

    def setUp(self):
        self.mm = MediaModel()
        self.mm.media_field.save("fname.xls", ContentFile("FILE-CONTENT"))
        self.mm.save()
        self.u = User(username='N')
        self.u.set_password('P')
        self.u.save()
        self.client.login(username='N', password='P')
        self.expected_media_url = (
            '/media/testapp/MediaModel/{}/media_field'.format(self.mm.pk))

    def test_url(self):
        self.assertEquals(self.mm.media_field.url, self.expected_media_url)

    def test_download_not_available(self):
        r = self.client.get(self.expected_media_url)
        self.assertEquals(r.status_code, 404)

    def test_download_available(self):
        self.u.is_superuser = True
        self.u.save()
        r = self.client.get(self.expected_media_url)
        self.assertEquals(r.status_code, 200)
        self.assertFalse(r.content)
        expected_headers = [ 
            r'X-Accel-Redirect: /internal_media/media_model_folder/fname(_\w+)?.xls',
            'X-Frame-Options: SAMEORIGIN',
            'Content-Type: application/vnd.ms-excel',
            r'Content-Disposition: attachment; filename=fname(_\w+)?.xls',
            'Vary: Cookie',
            ] 
        self.assertRegexpMatches(r.serialize_headers(), "\r\n".join(expected_headers))

