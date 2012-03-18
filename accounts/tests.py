"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from urlparse import urlparse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

class ViewsTest(TestCase):
    """
    TODO: Test login with douban / twitter
    """
    fixtures = ['auth_user.json']

    def test_signup(self):
        url = reverse("accounts_signup")
        url_failed = reverse("site_login")
        url_success = reverse("accounts_profile")

        # This url always redirect
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # email needed
        response = self.client.post(url,
                         {"username":"222", "password":"222"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # invalid email
        response = self.client.post(url,
                         {"username":"222", "password":"222", "email":"invalid_email"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # username already exists
        response = self.client.post(url,
                         {"username":"111", "password":"111", "email":"xxx@kindle.com"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # email already exists
        response = self.client.post(url,
                         {"username":"222", "password":"222", "email":"111@kindle.com"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # email already exists
        response = self.client.post(url,
                         {"username":"twitter_222", "password":"222", "email":"222@kindle.com"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # email already exists
        response = self.client.post(url,
                         {"username":"douban_222", "password":"222", "email":"222@kindle.com"})
        self.assertEqual(urlparse(response['Location']).path, url_failed)

        # created ok, redirect to accounts_profile page
        response = self.client.post(url,
                         {"username":"222", "password":"222", "email":"222@kindle.com"})
        self.assertEqual(urlparse(response['Location']).path, url_success)

    def test_profile(self):
        url = reverse("accounts_profile")
        self.client.login(username='111', password='111')
        response = self.client.post(url, {"first_name":"tom", "email":"111@kindle.com"})
        user = User.objects.get(username='111')
        self.assertEqual(user.first_name, 'tom')
        self.assertEqual(user.email, '111@kindle.com')

        # email used by others.
        response = self.client.post(url, {"email":"abc@kindle.com"})
        user = User.objects.get(username='111')
        self.assertEqual(user.email, '111@kindle.com')

        # Updated successfully
        response = self.client.post(url, {"first_name":"tom", "email":"xxx@kindle.com"})
        user = User.objects.get(username='111')
        self.assertEqual(user.email, 'xxx@kindle.com')
        

    def test_site_login(self):
        url = reverse("site_login")
        url_success = "/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Invalid username / password
        response = self.client.post(url, {'username':'222', 'password':'222'})
        self.assertEqual(urlparse(response['Location']).path, url)

        # Login with email / password
        response = self.client.post(url, {'username':'111@kindle.com', 'password':'111'})
        self.assertEqual(urlparse(response['Location']).path, url_success)
        self.client.logout()

        # Login with username / password
        response = self.client.post(url, {'username':'111', 'password':'111'})
        self.assertEqual(urlparse(response['Location']).path, url_success)
        self.client.logout()

    def test_site_logout(self):
        url = reverse("accounts_logout")
        home = "/"
        self.client.login(username='111', password='111')
        response = self.client.get(home)
        self.assertEqual(response.status_code, 200)
        
        self.client.get(url)
        response = self.client.get(home)
        self.assertEqual(response.status_code, 302)

