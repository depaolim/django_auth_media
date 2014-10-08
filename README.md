# README

Serving media based on authorization checks

Download the repo:

    git clone https://github.com/depaolim/django_auth_media.git

The app is tested on Django 1.6.7 and has no dependency from other packages (apart from django itself)


## Usage

Steps:

1. Add the folder django\_auth\_media to your PYTHONPATH

2. Use auth\_media.AuthMediaField in place of models.FileField

    from django.db import models
    from auth_media import AuthFileField

    class MediaModel(models.Model):
        media_field = AuthFileField(upload_to="media_model_folder")


3. Add urlpatterns in urls.py

    import auth_media
    urlpatterns += auth_media.urlpatterns()


4. Add MEDIA\_URL  and MEDIA\_ROOT in settings.py

    MEDIA_URL = '/media/'
    MEDIA_ROOT = 'path_to_files_on_file_system'


5. Add MEDIA\_REDIRECT in settings.py

    Use the same path used in "location" in nginx config. Example:

    settings.py:

        MEDIA_REDIRECT = "/internal_media"

    nginx.conf:

        location /internal_media {
            internal;
            alias /path_to_media_files;
        }


## Test

To run tests:

    cd testproj
    pip install -r requirements.txt
    python manage.py test testapp auth_media
