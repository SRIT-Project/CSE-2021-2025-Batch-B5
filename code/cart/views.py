from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Cart, CartItem
from shop.models import Product
from shop.models import Variation


def _cart_id(request):
    cart = request.session.session_key
    if not cart :
        cart = request.session.create()
    return cart

def rental_selection(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/cart/rental_selection.html', {'product': product})
def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)  # Get the product
    product_variation = []

    if request.method == 'POST':
        rental_type = request.POST.get('rental_type', 'hourly')  # Ensure rental_type is always set
        duration = int(request.POST.get('duration', 1))  # Default to 1 if not provided

        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product, 
                    variation_category__iexact=key, 
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except:
                pass

        # Calculate rental cost
        if rental_type == 'hourly':
            rental_cost = product.price * duration
        else:  # 'daily'
            rental_cost = 24 * product.price * duration

    if current_user.is_authenticated:
        # Check if the cart item already exists with the same rental_type and duration
        cart_item = CartItem.objects.filter(
            product=product, 
            user=current_user, 
            rental_type=rental_type, 
            duration=duration
        ).first()

        if cart_item:
            # Update existing cart item
            cart_item.quantity += 1
            cart_item.total_price += rental_cost
            cart_item.save()
        else:
            # Create a new cart item
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
                rental_type=rental_type,
                duration=duration,
                total_price=rental_cost
            )
        
        if product_variation:
            cart_item.variation.add(*product_variation)
        cart_item.save()

    else:  # If user is not authenticated (Guest User)
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

        # Check if the cart item already exists with the same rental_type and duration
        cart_item = CartItem.objects.filter(
            product=product, 
            cart=cart, 
            rental_type=rental_type, 
            duration=duration
        ).first()

        if cart_item:
            # Update existing cart item
            cart_item.quantity += 1
            cart_item.total_price += rental_cost
            cart_item.save()
        else:
            # Create a new cart item
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
                rental_type=rental_type,
                duration=duration,
                total_price=rental_cost
            )
        
        if product_variation:
            cart_item.variation.add(*product_variation)
        cart_item.save()

    return redirect('cart:cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1 :
            cart_item.quantity -= 1
            cart_item.save()
        else :
            cart_item.delete()
    except:
        pass

    return redirect('cart:cart')


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart:cart')
def cart(request, total_price=0, quantity=0, cart_items=None):
    grand_total = 0
    tax = 0

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            

            # Save total price to each cart item for display
            total_price += cart_item.sub_total()
            quantity += cart_item.quantity

    except ObjectDoesNotExist:
        pass

    tax = round((2 * total_price) / 100, 2)
    grand_total = total_price + tax
    handling = 15.00
    total = float(grand_total) + handling

    context = {
        'total': round(total_price, 2),
        'quantity': quantity,
        'cart_items': cart_items,
        'order_total': round(total, 2),
        'vat': tax,
        'handling': handling,
    }

    return render(request, 'shop/cart/cart.html', context)
