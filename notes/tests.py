"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

class ViewsTest(TestCase):
    fixtures = ['auth_user.json']

    def test_index(self):
        url_name = "notes_index"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 302)

        self.client.login(username="111", password="111")
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 200)

    def test_config(self):
        url_name = "notes_config"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 302)

        self.client.login(username="111", password="111")
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 302)

    def test_check(self):
        url_name = "notes_check"
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 403) # Require admin code
        response = self.client.post(reverse(url_name), {"a":"a"})
        self.assertEqual(response.status_code, 403) # Require admin code

