"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from urlparse import urlparse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

class ViewsTest(TestCase):
    fixtures = ['auth_user.json']
    def setup(self):
        self.client = Client()

    def test_signup(self):
        url_name = "accounts_signup"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 302)

        # username already exists
        response = self.client.post(reverse(url_name),
                         {"username":"111", "password":"111"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response['Location']).path, reverse("site_login"))

        # created ok, redirect to accounts_profile page
        response = self.client.post(reverse(url_name),
                         {"username":"222", "password":"222"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response['Location']).path, reverse("accounts_profile"))

