import os
import django
from django.apps import apps
from .apps import CartConfig


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import SimpleTestCase
from django.urls import reverse, resolve
from cart import views


from django.test import TestCase
from .models import Cart, CartItem

class CartModelTest(TestCase):
    def setUp(self):
        self.cart = Cart.objects.create(cart_id="test_cart")

    def test_cart_creation(self):
        self.assertEqual(self.cart.cart_id, "test_cart")
        self.assertIsInstance(self.cart, Cart)


class CartConfigTest(TestCase):
    def test_cart_config(self):
        self.assertEqual(CartConfig.name, 'cart')
        self.assertEqual(apps.get_app_config('cart').name, 'cart')

class CartURLsTest(SimpleTestCase):
    def test_cart_url(self):
        url = reverse('cart:cart')
        self.assertEqual(resolve(url).func, views.cart)

    def test_add_cart_url(self):
        url = reverse('cart:add_cart', args=[1])
        self.assertEqual(resolve(url).func, views.add_cart)

    def test_remove_cart_url(self):
        url = reverse('cart:remove_cart', args=[1, 1])
        self.assertEqual(resolve(url).func, views.remove_cart)

    def test_remove_cart_item_url(self):
        url = reverse('cart:remove_cart_item', args=[1, 1])
        self.assertEqual(resolve(url).func, views.remove_cart_item)