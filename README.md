KindleIO
========

A Kindle IO Service. Visit [http://kindle.io](http://kindle.io) for more details.

I Services:
-----------

- Push Hacker News articles to Kindle.
- Send article to Kindle via URLs.

O Services:
-----------

- Record your Kindle Highlights.


Requirements
------------

- [briticle](https://github.com/mitnk/briticle)

Run Unit Tests
==============

```
$ ./manage.py test accounts hackernews notes
```

Example of local_settings (the file):
-------------------------------------

```python
DEBUG = True
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = (
    "127.0.0.1",
)

LOG_ERROR_KINDLEIO = "/Users/mitnk/projects/kindleio/logs/errors.log"
LOG_INFO_KINDLEIO = "/Users/mitnk/projects/kindleio/logs/infos.log"

ADMINS = (
    ('mitnk', 'admin@admin.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'kindleio.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'laksjdlksdfasldkfj2239847sdlkfjas23l4j'

# Douban configs
DOUBAN_API_KEY='xxx'
DOUBAN_SECRET='xxx'

TWITTER_CONSUMER_KEY = 'xxx'
TWITTER_CONSUMER_SECRET = 'xxx'


# Secret key for kindleio internal API calls
API_SECRET_KEY = "xxx"

# Kindle.io sending email
KINDLEIO_EMAIL = "xxx"
KINDLEIO_EMAIL_PASSWD = "xxx"

HACKER_NEWS_DIR = "/Users/mitnk/kindleio/weekly/"
KINDLE_LIVE_DIR = "/Users/mitnk/kindleio/live/"

KINDLEIO_TWITTER_TOKEN = ""

ZONGHENG_DIR = "/Users/mitnk/kindleio/zongheng/"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'info_logger': {
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

```

