import requests

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages, auth   
from django.contrib.auth.decorators import login_required

from .forms import RegisterationFrom, UserForm, UserProfileForm
from .models import Account

# verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from .token import account_activation_token
from django.conf import settings
from django.contrib.auth import login as auth_login

import uuid

from cart.views import _cart_id
from cart.models import Cart, CartItem
from orders.models import Order
from .models import UserProfile
from orders.models import OrderProduct

from web3 import Web3
import json 
from web3.exceptions import ContractLogicError



w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:9545'))  # Default Ganache URL

# Ensure Web3 is connected
if not w3.is_connected():
    print("Web3 is not connected.")
    # Handle connection failure if needed

# Set the default account (use the first account from Ganache)
w3.eth.defaultAccount = w3.eth.accounts[0]  # Use the first account in Ganache's list

# Load contract ABI
contract_address = "0xC9A5557628c3d4b21e7BdC23751cEe427511acc4"  # Replace with your contract address
abi_file_path = 'blockchain/build/contracts/UserAuthentication.json'  # Path to ABI file

def load_contract_abi(file_path):
    with open(file_path, 'r') as abi_file:
        contract_json = json.load(abi_file)
        return contract_json['abi']

# Load ABI and create contract instance
contract_abi = load_contract_abi(abi_file_path)
contract = w3.eth.contract(address=contract_address, abi=contract_abi)


def register(request):
    if request.method == "POST":
        form = RegisterationFrom(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['Phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            # **Check if the user is already registered on blockchain**
            is_registered = contract.functions.isUserRegistered(email).call()

            if is_registered:
                messages.error(request, "User already registered. Please log in.")
                return redirect('/account/login/')  # Redirect to login page

            # **Create Django user only if not registered on blockchain**
            

            # **Register user on blockchain**
            try:
                gas_price = w3.eth.gas_price  # Get gas price automatically from Ganache

                tx = contract.functions.register(
                    email, first_name, last_name, phone_number, password
                ).transact({'from': w3.eth.defaultAccount})

                # Wait for the transaction to be confirmed
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx)

                print(f'Transaction hash: {tx_receipt.transactionHash.hex()}')

                user = Account.objects.create_user(
                first_name=first_name, last_name=last_name, email=email,
                username=username, password=password
                )
                user.Phone_number = phone_number
                user.save()

                # **Create user profile**
                profile = UserProfile(user_id=user.id)
                profile.save()

                # **Send account activation email**
                current_site = get_current_site(request)
                subject = 'Please activate your account'
                message = render_to_string('shop/accounts/email_activate/account_verification_email.html', {
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                to_email = email
                send_email = EmailMessage(subject, message, to=[to_email])
                send_email.send()

                return redirect('/account/register/?command=verification&email=' + email)

            except ContractLogicError as e:
                error_message = str(e)
                if "User already registered" in error_message:
                    messages.error(request, "User is already registered on the blockchain. Please log in.")
                    return redirect('/account/login/')
                else:
                    messages.error(request, "Blockchain transaction failed. Please try again.")
                    user.delete()  # Rollback user creation in Django
                    return redirect('/account/register/')

    else:  # If it's a GET request
        form = RegisterationFrom()

    context = {'forms': form}
    return render(request, 'shop/accounts/register.html', context)

def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Check if user is registered on blockchain
            is_registered = contract.functions.isUserRegistered(email).call()
            if not is_registered:
                messages.error(request, "User not found on blockchain. Please register first.")
                return redirect('accounts:register')

            # Get blockchain address associated with email
            user_address = contract.functions.getAddressByEmail(email).call()

            # Authenticate user in Django
            user = auth.authenticate(email=email, password=password)

            if user is not None:
                if not user.is_active:
                    messages.warning(request, "Your account is not activated. Please check your email and activate your account before logging in.")
                    return redirect('accounts:login')

                # Cart merging logic
                try:
                    cart = Cart.objects.get(cart_id=_cart_id(request))
                    is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                    if is_cart_item_exists:
                        cart_item = CartItem.objects.filter(cart=cart)

                        # Get product variations by cart ID
                        product_variation = [list(item.variation.all()) for item in cart_item]

                        # Get existing cart items for the user
                        user_cart_items = CartItem.objects.filter(user=user)
                        ex_var_list = [list(item.variation.all()) for item in user_cart_items]
                        id_list = [item.id for item in user_cart_items]

                        for pr in product_variation:
                            if pr in ex_var_list:
                                index = ex_var_list.index(pr)
                                item_id = id_list[index]
                                item = CartItem.objects.get(id=item_id)
                                item.quantity += 1
                                item.user = user
                                item.save()
                            else:
                                for item in cart_item:
                                    item.user = user
                                    item.save()
                except Exception as e:
                    print(f"Cart merge error: {str(e)}")

                auth_login(request, user)

                # Redirect to next page if applicable
                url = request.META.get('HTTP_REFERER')
                try:
                    query = requests.utils.urlparse(url).query
                    params = dict(x.split('=') for x in query.split('&'))
                    if 'next' in params:
                        return redirect(params['next'])
                except:
                    return redirect('accounts:dashboard')
                return redirect('accounts:dashboard')
            else:
                # Check if user exists but is inactive
                if Account.objects.filter(email=email, is_active=False).exists():
                    messages.warning(request, "Your account is not activated. Please check your email and activate it before logging in.")
                else:
                    messages.error(request, "Incorrect email or password.")
                
                return redirect('accounts:login')

        except ContractLogicError as e:
            messages.error(request, f"Blockchain error: {str(e)}")
            return redirect('accounts:login')

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('accounts:login')

    return render(request, 'shop/accounts/login.html')



@login_required(login_url = 'accounts:login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You've successfully logged out . Come back soon!")
    return redirect('accounts:login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    user.is_active = True
    user.save()
    messages.success(request, "Your account is activated, log in and let's go.")
    return redirect('accounts:login')

@login_required(login_url = 'accounts:login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    profile = UserProfile.objects.get(user_id=request.user.id)
    
    orders_count = orders.count()
    context = {
        'orders_count':orders_count,
        'profile':profile,
        
    }
    return render(request, 'shop/accounts/dashboard/dashboard.html', context)



@login_required(login_url = 'accounts:login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()
    
    context = {
        'orders':orders,
        'orders_count':orders_count,
    }
    return render(request, 'shop/accounts/dashboard/my_orders.html', context)


@login_required(login_url = 'accounts:login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'shop/accounts/dashboard/edit_profile.html', context)


@login_required(login_url = 'accounts:login')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        repeat_new_password = request.POST['repeat_new_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == repeat_new_password:
            success = user.check_password(old_password)
            if success :
                user.set_password(new_password)
                user.save()
                auth.login(request, user)
                messages.success(request, 'Password Updated successfully.')
                return redirect('accounts:change_password')
            else:
                messages.error(request, 'Old password is wrong')
                return redirect('accounts:change_password')
        else:
            messages.error(request, 'Password does not match')
            return redirect('accounts:change_password')
    return render(request, 'shop/accounts/dashboard/change_password.html')


@login_required(login_url = 'accounts:login')
def order_detail(request,order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    subtotal = 0
    for x in order_detail:
        subtotal += x.product_price * x.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'shop/accounts/dashboard/order_detail.html', context)


def forget_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            
            # SEND EMAIL
            current_site = get_current_site(request)
            subject = 'Reset Your Password'
            message = render_to_string('shop/accounts/forget_password/send_resetpassword_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(subject, message, to=[to_email])
            send_email.send()

            # essages.success(request, "We sent a verification message to your email, click verify it, and let's start")
            
            
            return redirect('/account/forget_password/?command=resetpassword&email='+email)
        else: 
            messages.error(request, 'This email does not exist!')
            return redirect('accounts:forget_password')

    return render(request, 'shop/accounts/forget_password/forget_password.html') 


def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        request.session['uid'] = uid
        return redirect('accounts:reset_password')
    else:
        messages.error(request, 'This is link has been expired !')
        return redirect('accounts:forget_password')



def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        repeat_password = request.POST['confirm_password']

        try:
            if password == repeat_password:
                uid = request.session.get('uid')
                user = Account.objects.get(pk=uid)
                user.set_password(password)
                user.save()
                messages.success(request, 'Password Reset Successful')
                return redirect('accounts:login')
            else:
                messages.error(request, "Password does not match!")
                return redirect('accounts:reset_password')
        except Account.DoesNotExist:
            messages.error(request, "Please enter your email address here first! ")
            return redirect('accounts:forget_password')

    else:
        return render(request, 'shop/accounts/forget_password/reset_password.html')