from django.db import models

from auth_media import AuthFileField


class MediaModel(models.Model):
    interim_media = AuthFileField(upload_to="interim")
    xaccell_media = AuthFileField(upload_to="xaccell", media_server='xaccell')
    secure_media = AuthFileField(upload_to="secure", media_server='secure')
