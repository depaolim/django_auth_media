from django.db import models

from auth_media import AuthFileField


class MediaModel(models.Model):
    slow_media = AuthFileField(upload_to="slow")
    xaccell_media = AuthFileField(upload_to="xaccell", engine='xaccell')
    secure_media = AuthFileField(upload_to="secure", engine='secure')
