"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from urlparse import urlparse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from kindleio.hackernews.models import HackerNews, SendRecord


class ViewsTest(TestCase):
    fixtures = ['auth_user.json']

    def test_config(self):
        # Need login
        url_name = "hackernews_config"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response['Location']).path, reverse("site_login"))

        # username already exists
        self.client.login(username="111", password="111")
        response = self.client.post(reverse(url_name),
                         {"receive_hn":"on", "points_limit":"500"})
        self.assertEqual(urlparse(response['Location']).path, reverse("accounts_profile"))

    def test_fetch(self):
        url_name = "hackernews_fetch"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 403) # Require admin code
        response = self.client.post(reverse(url_name), {"a":"a"})
        self.assertEqual(response.status_code, 403) # Require admin code

    def test_check_for_sending(self):
        url_name = "hackernews_check_for_sending"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 403) # Require admin code
        response = self.client.post(reverse(url_name), {"a":"a"})
        self.assertEqual(response.status_code, 403) # Require admin code

        response = self.client.post(reverse(url_name), 
                                    {"key": settings.API_SECRET_KEY, "a":"a"})
        self.assertEqual(response.status_code, 200)


