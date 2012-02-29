"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from models import POINTS_LIMITS, POINTS_LIMIT_PAIRS

class HackerNewsTest(TestCase):
    def test_points_limits(self):
        for i, pair in enumerate(POINTS_LIMIT_PAIRS):
            self.assertEqual(pair[0], POINTS_LIMITS[i])
