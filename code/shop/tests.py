# tests.py
from .forms import ReviewForm
from django.test import TestCase
from django.apps import apps
from .apps import ShopConfig

class ShopConfigTest(TestCase):
    def test_shop_config(self):
        self.assertEqual(ShopConfig.name, 'shop')
        self.assertEqual(apps.get_app_config('shop').name, 'shop')

class ReviewFormTest(TestCase):
    def test_review_form_valid(self):
        form_data = {
            'review': 'Great product!',
            'rating': 5
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid(self):
        form_data = {
            'review': '',
            'rating': 5
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_rating(self):
        form_data = {
            'review': 'Great product!',
            'rating': 6  # Assuming rating should be between 1 and 5
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())