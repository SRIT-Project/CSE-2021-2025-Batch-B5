from decimal import Decimal
import json
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.contrib import messages


from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from shop.models import Product


import razorpay
from django.http import JsonResponse
from django.conf import settings
from .models import Order
@login_required(login_url = 'accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html',)


def terms_conditions(request):
    return render(request, "shop/orders/terms_conditions.html")

@login_required(login_url = 'accounts:login')
def checkout(request,total=0, total_price=0, quantity=0, cart_items=None):
    tax = 0.00
    handing = 0.00
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        total_price = Decimal(0)
        quantity = 0

        # Calculate total price considering rental type and duration
        for cart_item in cart_items:
            rental_type = cart_item.rental_type
            duration = cart_item.duration
            price = Decimal(cart_item.product.price)
            item_quantity = cart_item.quantity

            if rental_type == "hourly":
                total_price += price * duration * item_quantity  # Price * Duration * Quantity for hourly rental
            elif rental_type == "daily":
                total_price += price * 24 * duration * item_quantity  # Price * 24 * Duration * Quantity for daily rental
            else:
                total_price += price * item_quantity  # Regular price for non-rental items

            quantity += item_quantity

        # Add handling charges to the total price
        handing = Decimal(15.00)
        subtotal = total_price + handing  # Subtotal before tax and any additional fees

        # Calculate tax (example: 2% of total price)
        tax = round((2 * total_price) / 100, 2)

        # Calculate the grand total (subtotal + tax)
        grand_total = subtotal + tax
        
        # Add shipping/handling fees to the grand total
        total = grand_total 
    except ObjectDoesNotExist:
        pass # just ignore

    
    tax = round(((2 * total_price)/100), 2)
    grand_total = total_price + tax
    handing = 15.00
    total = float(grand_total) + handing
    
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items':cart_items,
        'handing': handing,
        'vat' : tax,
        'order_total': total,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)

def create_razorpay_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        order_id = data.get("orderID")
        order = Order.objects.get(order_number=order_id)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create order in Razorpay
        razorpay_order = client.order.create({
            "amount": int(order.order_total * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": "1"  # Auto capture
        })

        return JsonResponse({
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"]
        })
    
@login_required(login_url = 'accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    handing = 15.0
    # if the cart count is less than 0, redirect to shop page 
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        # Adjust total based on rental_type and duration
        if cart_item.rental_type == "hourly":
            total += (cart_item.product.price * cart_item.duration * cart_item.quantity)
        elif cart_item.rental_type == "daily":
            total += (24 * cart_item.product.price * cart_item.duration * cart_item.quantity)
        else:
            total += (cart_item.product.price * cart_item.quantity)
        
        quantity += cart_item.quantity

    # Calculate tax and grand total
    tax = round(((2 * total)/100), 2)
    grand_total = total + tax
    handing = 15.0
    total = float(grand_total) + handing
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # shop all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            


            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'handing': handing,
                'vat': tax,
                'order_total': total,
            }
            return render(request, 'shop/orders/checkout/payment.html', context)
        else:
            messages.error(request, 'YOur information not Vailed')
            return redirect('orders:checkout')
            
    else:
        return redirect('shop:shop')

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    
    # Store transaction details in the Payment model
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        status=body['status'],
        amount_paid=order.order_total,
    )
    
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()
    
    # Move cart items to OrderProduct table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct(
            order_id=order.id,
            payment=payment,
            user_id=request.user.id,
            product_id=item.product_id,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True
        )
        order_product.save()
        
        # Add variation to OrderProduct table
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        order_product.variations.set(product_variation)
        order_product.save()

        # Reduce stock of sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear Cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order details back to frontend
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotall = 0
        for i in ordered_products:
            subtotall += i.product_price * i.quantity
        subtotal = round(subtotall, 2)
        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist) as e:
        print(f"Exception occurred: {e}")
        return redirect('shop:shop')
