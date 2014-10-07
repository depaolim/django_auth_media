# README

Serving media based on authorization checks

Download the repo:

    git clone https://github.com/depaolim/django_auth_media.git

Add the folder django\_auth\_media to your pythonpath

The app is tested on Django 1.6.7 and has no dependency from other packages (apart from django itsef)


## Usage

Steps:

1. Add the app django\_auth\_media to INSTALLED\_APPS in settings.py

2. Add MEDIA\_URL  and MEDIA\_ROOT in settings.py

3. Add MEDIA\_REDIRECT in settings.py

    Use the same path used in "location" in nginx config. Example:

    settings.py:

        MEDIA_REDIRECT = "/internal_media"

    nginx.conf:

        location /internal_media {
            internal;
            alias /home/dslcm_data/dslcm_media;
        }


4. Add urlpatters in urls.py

5. Use auth\_media.AuthMediaField in place of models.FileField


## Test

To run tests:

    pip install -r requirements.txt
    python manage.py test
