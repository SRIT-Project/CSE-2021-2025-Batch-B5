# tests.py

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import TestCase
from .forms import OrderForm

from django.test import SimpleTestCase
from django.urls import reverse, resolve
from orders import views


class OrderFormTest(TestCase):
    def test_order_form_valid(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890',
            'email': 'john.doe@example.com',
            'address': '123 Main St',
            'country': 'USA',
            'state': 'NY',
            'city': 'New York',
            'order_note': 'Please deliver between 9 AM and 5 PM'
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_order_form_invalid(self):
        form_data = {
            'first_name': '',
            'last_name': 'Doe',
            'phone': '1234567890',
            'email': 'john.doe@example.com',
            'address': '123 Main St',
            'country': 'USA',
            'state': 'NY',
            'city': 'New York',
            'order_note': 'Please deliver between 9 AM and 5 PM'
        }
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_order_form_missing_email(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890',
            'email': '',
            'address': '123 Main St',
            'country': 'USA',
            'state': 'NY',
            'city': 'New York',
            'order_note': 'Please deliver between 9 AM and 5 PM'
        }
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_order_form_invalid_phone(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': 'invalid_phone',
            'email': 'john.doe@example.com',
            'address': '123 Main St',
            'country': 'USA',
            'state': 'NY',
            'city': 'New York',
            'order_note': 'Please deliver between 9 AM and 5 PM'
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_order_form_missing_address(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '1234567890',
            'email': 'john.doe@example.com',
            'address': '',
            'country': 'USA',
            'state': 'NY',
            'city': 'New York',
            'order_note': 'Please deliver between 9 AM and 5 PM'
        }
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())

class OrdersURLsTest(SimpleTestCase):
    def test_payment_method_url(self):
        url = reverse('orders:payment_method')
        self.assertEqual(resolve(url).func, views.payment_method)

    def test_checkout_url(self):
        url = reverse('orders:checkout')
        self.assertEqual(resolve(url).func, views.checkout)

    def test_payment_url(self):
        url = reverse('orders:payment')
        self.assertEqual(resolve(url).func, views.payment)

    def test_payments_url(self):
        url = reverse('orders:payments')
        self.assertEqual(resolve(url).func, views.payments)

    def test_order_completed_url(self):
        url = reverse('orders:order_complete')
        self.assertEqual(resolve(url).func, views.order_completed)