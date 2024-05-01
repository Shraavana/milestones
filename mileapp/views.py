from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.contrib.auth import update_session_auth_hash
import random
from payment.forms import AddressForm
from django.db.models import F 
from django.db.models import OuterRef, Subquery
from .context_processors import *
from django.contrib.auth import authenticate, logout,login
from django.core.mail import send_mail
from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import datetime
from datetime import datetime, timedelta
from django.http import  HttpResponseRedirect
from django.http import JsonResponse
from django.db.models import Sum,Count
from adminhome.models import Coupon
from payment.models import Address,CartOrder,CartItem,ProductOrder
from .models import Product,category,User,ProductImages,ProductAttribute,Color,WishlistItem
from mileapp.models import category
from payment.models import Wallet,WalletHistory
from adminhome.models import ProductOffer,CategoryOffer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import string

from .forms import UserProfileForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from mileapp.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode




#===============================user index==============================================================================================================================================================

from django.db.models import F


@cache_control(max_age=0, no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def user_index(request):

    products = Product.objects.filter(featured=True)
    # .order_by('-id').distinct()
    
    if request.session.get('order_placed', False):
        del request.session['order_placed']
        print(products)
        return redirect('indexuser:user_index') 

    context = {
        'products': products,
    }
    
    return render(request,'userhome/index.html',context)



#============================ otp generate function =============================================================================================================================================================

def generate_otp():
    otp = str(random.randint(100000, 999999))
    timestamp = str(timezone.now())  
    return otp, timestamp

#============================= user signup ======================================================================================================================================================================

def signup(request):
    if request.user.is_authenticated:
        return redirect('user_index')
    if request.method == 'POST':
        username=request.POST.get('username')
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        password=request.POST.get('password')
        cpassword=request.POST.get('cpassword')

        if User.objects.filter(username=username).exists():
            messages.error(request,'Username is already existing . please choose a different username')
            return render(request, 'userhome/usersignup.html')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email is alrady existing so Please choose another')
            return render(request, 'userhome/usersignup.html')
        elif cpassword != password:
            messages.error(request, 'mismatch password')
            return render(request, 'userhome/usersignup.html')

        otp, timestamp = generate_otp()
        
        request.session['signup_otp'] = otp  
        request.session['otp_timestamp'] = timestamp 

        send_mail(
            'OTP verification',
            f'your OTP for signup is : {otp}',
            'yourseamlesslife@gmail.com',
            [email],
            fail_silently=False
        )
        request.session['signup_details']={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'password': make_password(password),
        }

        return redirect('indexuser:enter_otp')
    return render(request,'userhome/usersignup.html')
#=================================================================changepassword===========================================================
@login_required


def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if the current password is correct
        if not request.user.check_password(current_password):
            messages.warning(request, 'Incorrect current password. Please try again.')
            return redirect('change_password')

        # Custom password validation function
        # Check if the password length is at least 8 characters
        if len(new_password) < 8:
            messages.warning(request, 'Password must be at least 8 characters long.')
            return redirect('indexuser:change_password')

        # Check if the password contains at least one special character
        special_characters = set(string.punctuation)
        if not any(char in special_characters for char in new_password):
            messages.warning(request, 'Password must contain at least one special character.')
            return redirect('indexuser:change_password')

        # Check if the password contains any whitespace characters
        if ' ' in new_password:
            messages.warning(request, 'Password cannot contain whitespace characters.')
            return redirect('indexuser:change_password')

        # Validate the new password
        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            messages.warning(request, e)
            return redirect('indexuser:change_password')

        # Check if new password matches the confirmation
        if new_password != confirm_password:
            messages.warning(request, 'New password and confirmation do not match. Please try again.')
            return redirect('indexuser:change_password')

        # Set the new password and save
        request.user.set_password(new_password)
        valuser = request.user.save()
        if valuser:
            messages.success(request, 'the password changed sucessfully')
        # Update session auth hash

        update_session_auth_hash(request, request.user)

        # Logout the user for security reasons
        logout(request)

        # Redirect to the logout page
        return redirect('indexuser:user_logout')

    return render(request, 'userhome/change_password.html')



#===================================================== enter otp that we recive in the mail ================================================================================================================================

from datetime import datetime, timedelta
from django.utils import timezone

def enter_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('signup_otp')
        timestamp_str = request.session.get('otp_timestamp')

        if not timestamp_str or not isinstance(timestamp_str, str):
            messages.error(request, 'Invalid or missing OTP timestamp.')
            return render(request, 'userhome/otp.html')

        try:
            expiration_time = datetime.fromisoformat(timestamp_str) + timedelta(minutes=1)
        except ValueError:
            messages.error(request, 'Invalid OTP timestamp format.')
            return render(request, 'userhome/otp.html')

        current_time = timezone.now()

        if current_time > expiration_time:
            messages.error(request, 'OTP has expired. Please request a new one.')
            return render(request, 'userhome/otp.html')

        if entered_otp == stored_otp:
            new_user = User.objects.create_user(
                username=request.session['signup_details']['username'],
                email=request.session['signup_details']['email'],
                first_name=request.session['signup_details']['first_name'],
                last_name=request.session['signup_details']['last_name'],
                phone=request.session['signup_details']['phone'],
                password=request.session['signup_details']['password']
            )
            login(request, new_user)

            # Clean up session data after successful registration
            request.session.pop('signup_otp', None)
            request.session.pop('otp_timestamp', None)
            request.session.pop('signup_details', None)

            return redirect('indexuser:user_index')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    # Remaining time calculation
    timestamp_str = request.session.get('otp_timestamp')
    expiration_time = datetime.fromisoformat(timestamp_str) + timedelta(minutes=1)
    current_time = timezone.now()
    remaining_time = max(timedelta(0), expiration_time - current_time)
    remaining_minutes, remaining_seconds = divmod(remaining_time.seconds, 60)

    return render(request, 'userhome/otp.html', {'remaining_minutes': remaining_minutes, 'remaining_seconds': remaining_seconds})

#====================================if the otp expire resend the otp===============================================================================================================
def resend_otp(request):
    if 'signup_details' in request.session:
        otp, timestamp = generate_otp()

        request.session['signup_otp'] = otp
        request.session['otp_timestamp'] = timestamp

        send_mail(
            'Resent OTP verification',
            f'Your new OTP for signup is: {otp}',
            'shraavana09@gmail.com',
            [request.session['signup_details']['email']],
            fail_silently=True
        )
        messages.info(request, 'New OTP sent. Please check your email.')
        return redirect('indexuser:enter_otp')
    else:
        messages.error(request, 'No signup session found.')
        return redirect('indexuser:signup')

#========================user signin to the system====================================================================================================================================================
@cache_control(max_age=0, no_cache=True, must_revalidate=True, no_store=True)
@never_cache  
def signin(request):
    if request.user.is_authenticated:
        return redirect('user_index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Try to get the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        # Authenticate the user
        if user is not None:
            authenticated_user = authenticate(request, email=email, password=password)
            if authenticated_user is not None:
                if authenticated_user.is_active:
                    login(request, authenticated_user)
                    return redirect('indexuser:user_index')
                else:
                    messages.error(request, 'Your account is Blocked by the admin')
            else:
                messages.error(request, 'Invalid password')
        else:
            messages.error(request, 'User does not exist')
    
    return render(request, 'userhome/userlogin.html')
#===================================================forgot password=====================================================================

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'userhome/forgot_password.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        if user is not None:
            # Generate a token for password reset
            token = default_token_generator.make_token(user)

            # Encode user id for the password reset link
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Send password reset email to the user
            reset_link = request.build_absolute_uri(
                f'/reset-password/{uid}/{token}/'
            )
            subject = 'Password Reset'
            message = render_to_string('userhome/reset_password_email.html', {
                'user': user,
                'reset_link': reset_link
            })
            send_mail(subject, message, 'yourseamlesslife@gmail.com', (user.email,))

            messages.info(request, 'Password reset instructions have been sent to your email.')
            return redirect('indexuser:user_login')
        else:
            messages.error(request, 'No user found with that email address.')

    return render(request, 'userhome/forgot_password.html')
#===================================reset password======================================================================================
def reset_password(request, uidb64, token):
    if request.method == 'POST':
        # Decode user id from uidb64
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            # Validate new password
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            try:
                validate_password(new_password)
            except ValidationError as e:
                messages.error(request, ', '.join(e.messages))
                return render(request, 'userhome/reset_password.html', {'uidb64': uidb64, 'token': token})

            if new_password != confirm_password:
                messages.error(request, 'New password and confirm password do not match.')
                return render(request, 'userhome/reset_password.html', {'uidb64': uidb64, 'token': token})

            # Set the new password and save
            user.password = make_password(new_password)
            user.save()

            messages.success(request, 'Password reset successful. You can now login with your new password.')
            return redirect('signin')
        else:
            messages.error(request, 'Invalid reset link. Please try again.')
            return render(request, 'userhome/reset_password.html')

    # GET request, render reset password form
    return render(request, 'userhome/reset_password.html', {'uidb64': uidb64, 'token': token})





#============================user signout==================================================================================================================================================================================================
@cache_control(max_age=0, no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def user_logout(request):
    logout(request)
    return redirect('indexuser:user_login')

#=============================display the all product in shop================================================================================================================================
def shop(request, category_id=None,brand_id=None):
    all_categories = category.objects.filter(is_deleted=False,is_blocked=False)
    selected_category = None
    selected_brand = None
    products = None
    product_count = None
    brands = Brand.objects.filter(is_active=True)
    try:
        discount_offer = ProductOffer.objects.get(active=True)
    except ProductOffer.DoesNotExist:
        discount_offer = None
        
    try:
        
        discounted_offer = CategoryOffer.objects.filter(active=True)
    except ProductOffer.DoesNotExist:
        discounted_offer = None
    if discounted_offer:
        for dis in discounted_offer:
            products_with_discount = Product.objects.filter(category=dis.category, is_available=True)
            current_date = timezone.now()
            if current_date > dis.end_date:
                dis.active = False
                dis.save()
                
    if 'category_id' in request.GET:
        category_id = request.GET['category_id']
        selected_category = get_object_or_404(category, id=category_id)
        products = Product.objects.filter(
            category=selected_category,
            is_available=True,
            is_deleted=False,
            brand__is_active=True,
            category__is_deleted=False,
            category__is_blocked=False
        )
        product_count = products.count()

    elif 'brand_id' in request.GET:
        brand_id = request.GET['brand_id']
        selected_brand = get_object_or_404(Brand, id=brand_id)
        products = Product.objects.filter(
            brand=selected_brand,
            is_available=True,
            is_deleted=False,
            brand__is_active=True,
            category__is_deleted=False,
            category__is_blocked=False
        )
        product_count = products.count()

    else:
        products = Product.objects.filter(is_available=True, is_deleted=False, brand__is_active=True ,category__is_deleted=False,category__is_blocked=False)
        product_count = products.count()

   
    context = {
        'products': products,
        'product_count': product_count,
        'all_categories': all_categories,
        'selected_category': selected_category,
        'discount_offer':discount_offer,
        "discounted_offer":discounted_offer,
        'selected_brand': selected_brand,
        'brands': brands,
        
        
    }

    return render(request, 'userhome/shop.html', context)
#===============================================================shop filter================================================================
def shop0(request):
    products = Product.objects.all().order_by('product_name')
    context = {'products': products}
    return render(request,'userhome/shop.html',context)
def shop1(request):
    products = Product.objects.all().order_by('-product_name')
    context = {'products':products}
    return render(request,'userhome/shop.html',context)

def shop_ase_price(request):
    products = Product.objects.filter(productattribute__is_deleted=False).annotate(max_price=F('productattribute__price')).order_by('-max_price')
    context = {'products': products}
    return render(request, 'userhome/shop.html', context)

def shop_des_price(request):
    products = Product.objects.filter(productattribute__is_deleted=False).annotate(min_price=F('productattribute__price')).order_by('min_price')
    context = {'products': products}
    return render(request, 'userhome/shop.html', context)

#===============================click the product it view the product details==================================================================================================================================================

def product_details(request, product_id,category_id=None):
    user=request.user
    product = Product.objects.get(id=product_id)
    images = ProductImages.objects.filter(product=product)
    related_product=Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    colors = ProductAttribute.objects.filter(product=product).distinct()

    try:   
        discount_offer = ProductOffer.objects.get(active=True)
    except ProductOffer.DoesNotExist:
        discount_offer = None
                        
    try:
        discounted_offer = CategoryOffer.objects.filter(active=True)
    except ProductOffer.DoesNotExist:
        discounted_offer = None
    if discounted_offer:
        for dis in discounted_offer:
            products_with_discount = Product.objects.filter(category=dis.category, is_available=True)
            current_date = timezone.now()
            if current_date > dis.end_date:
                dis.active = False
                dis.save()

    if request.method=="POST":
        if user.is_authenticated:
            print("request entered ")
            colour=request.POST.get('colorselect')
            qty=request.POST.get('quantity')
            product_colour=Color.objects.get(color_name=colour)
            products=ProductAttribute.objects.get(product=product,color=product_colour)
           
            print("Related Products:", related_product)
        else:
            return redirect('user_login')

    
    context={
        'product': product,
        'related_product': related_product,
        'colors' :colors,
        'images':images,
        "discount_offer":discount_offer,
        "discounted_offer":discounted_offer,
    }
    

    return render(request, 'userhome/product_detailes.html', context)

@login_required(login_url='user_login')
def add_to_cart(request):
    user = request.user
    address = Address.objects.filter(users = user).first()
    
    if request.method == 'POST':
        product_id = request.POST.get('item_id')
        color_name = request.POST.get('product_color')

        qty = int(request.POST.get('quantity'))  

        try:
            color = Color.objects.get(color_name=color_name)
            product = ProductAttribute.objects.get(product=product_id, color=color)
        except (Color.DoesNotExist, ProductAttribute.DoesNotExist):
            messages.error(request, 'Invalid product or color.')
            return JsonResponse({'status': 'error', 'message': 'Invalid product or color.'}, status=400)
        
        if qty > product.stock:
            messages.error(request, f"Insufficient stock. Only {product.stock} available.")
            response_data = {
                'status': 'error',
                'message': f"Insufficient stock. Only {product.stock} available."
            }
            return JsonResponse(response_data)

        try:
            cart_item = CartItem.objects.get(product=product, user=user, is_deleted=False)
            available_stock = product.stock - cart_item.quantity
            if qty > available_stock:
                messages.error(request, f"Stock limit reached. Only {available_stock} available.")
                response_data = {
                    'status': 'error',
                    'message': f"Stock limit reached. Only {available_stock} available."
                }
                return JsonResponse(response_data)

            cart_item.quantity += qty
            cart_item.total = product.price * cart_item.quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            item, created = CartItem.objects.get_or_create(user=user, product=product,address=(address.get_address() if address else None) , defaults={'is_deleted': False})
            item.quantity = qty
            item.total = product.price * qty
            item.save()

        cart_count = CartItem.objects.filter(user=request.user, is_deleted=False).count()

        response_data = {
            'status': 'success',
            'message': 'Product added to cart successfully',
            'cart_count': cart_count
        }
        return JsonResponse(response_data)
    else:
        print('Invalid request or not AJAX') 
        return JsonResponse({'status': 'error', 'message': 'Invalid request or not AJAX'}, status=400)



#======================================== cart-list page ============================================================================================================================================================================
@login_required(login_url='user_login')  
@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
 
def cart_list(request):
    user = request.user
    items = CartItem.objects.filter(user=user, is_deleted=False)
    coupons = Coupon.objects.all()
    ct = items.count()

    total_without_discount = items.aggregate(total_sum=Sum('total'))['total_sum'] or 0

    discounts = 0

    applied_coupon_id = request.session.get('applied_coupon_id')

    if request.session.get('order_placed', False):
        del request.session['order_placed']
       

    if applied_coupon_id:
        try:
            applied_coupon = Coupon.objects.get(id=applied_coupon_id, active=True,
                                                active_date__lte=timezone.now(), expiry_date__gte=timezone.now())
            discounts = (total_without_discount * applied_coupon.discount) / 100
        except Coupon.DoesNotExist:

            request.session.pop('applied_coupon_id', None)

    if request.method == "POST":
        if 'apply_coupon' in request.POST:
            coupon_code = request.POST.get('coupon_code')
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True, active_date__lte=timezone.now(),
                                            expiry_date__gte=timezone.now())

                discounts = (total_without_discount * coupon.discount) / 100
                items.update(coupon=coupon)

                request.session['applied_coupon_id'] = coupon.id

                messages.success(request, 'Coupon applied successfully!')
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid or expired coupon code')

        elif 'remove_coupon' in request.POST:

            request.session.pop('applied_coupon_id', None)

            total_without_discount = items.aggregate(total_sum=Sum('total'))['total_sum'] or 0
            discounts = 0

            applied_coupon_id = request.session.get('applied_coupon_id')
            if applied_coupon_id:
                try:
                    applied_coupon = Coupon.objects.get(id=applied_coupon_id, active=True,
                                                        active_date__lte=timezone.now(), expiry_date__gte=timezone.now())
                    discounts = (total_without_discount * applied_coupon.discount) / 100
                except Coupon.DoesNotExist:
                    request.session.pop('applied_coupon_id', None)

            items.update(coupon=None)

            total_after_discount = total_without_discount - discounts
            data = {
                'success': True,
                'totals': total_without_discount,
                'discounts': discounts,
                'total': total_after_discount,
            }

            messages.success(request, 'Coupon removed successfully!')
                    
    total_after_discount = total_without_discount - discounts

    context = {
        'items': items,
        'totals': total_without_discount,
        'total': total_after_discount,
        'ct': ct,
        'coupons': coupons,
        'discounts': discounts,
    }

    request.session['totals'] = total_without_discount
    request.session['total'] = total_after_discount
    request.session['discounts'] = discounts


    return render(request, 'userhome/cart.html', context)


def remove_coupon(request):
    try:

        request.session.pop('applied_coupon_id', None)

  
        user = request.user
        items = CartItem.objects.filter(user=user, is_deleted=False)
        items.update(coupon=None)

    
        total_without_discount = items.aggregate(total_sum=Sum('total'))['total_sum'] or 0
        discounts = 0


        applied_coupon_id = request.session.get('applied_coupon_id')
        if applied_coupon_id:
            try:
                applied_coupon = Coupon.objects.get(id=applied_coupon_id, active=True,
                                                    active_date__lte=timezone.now(), expiry_date__gte=timezone.now())
                discounts = (total_without_discount * applied_coupon.discount) / 100
            except Coupon.DoesNotExist:
                request.session.pop('applied_coupon_id', None)

        total_after_discount = total_without_discount - discounts
        
        data = {
            'success': True,
            'totals': total_without_discount,
            'discounts': discounts,
            'total': total_after_discount,
        }

        messages.success(request, 'Coupon removed successfully!')

    except Exception as e:
        data = {'success': False, 'error': str(e)}

    return JsonResponse(data)


#========================================= qunatity updation and delete cart item ================================================================================================================================================

@login_required(login_url='user_login')
def qty_update(request):
    user = request.user
    item_id = request.GET.get('item_id')
    new_quantity = int(request.GET.get('new_quantity'))

    cart_item = get_object_or_404(CartItem, id=item_id)
    now = timezone.now()

    if new_quantity > cart_item.product.stock:
        return JsonResponse({'error': 'Insufficient stock.', 'success': False}, status=400)

    cart_item.quantity = new_quantity
    cart_item.total = cart_item.product.price * new_quantity
    cart_item.save()

    total_without_discount = CartItem.objects.filter(user=user, is_deleted=False).aggregate(total_sum=Sum('total'))['total_sum'] or 0

    discounts = 0
    applied_coupon_id = request.session.get('applied_coupon_id')
    if applied_coupon_id:
        try:
            applied_coupon = Coupon.objects.get(id=applied_coupon_id, active=True,
                                                active_date__lte=timezone.now(), expiry_date__gte=timezone.now())
            discounts = (total_without_discount * applied_coupon.discount) / 100
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon_id', None)

    total_after_discount = total_without_discount - discounts

    response_data = {
        'new_qty': new_quantity,
        'new_price': cart_item.total,
        'totals': total_without_discount,
        'discounts': discounts,
        'total': total_after_discount
    }
    return JsonResponse(response_data)

@login_required(login_url='user_login')
def delete_cart_item(request):
    user = request.user
    item_id = request.GET.get('item_id')

    try:
        cart_item = CartItem.objects.get(id=item_id, user=user)
        cart_item.delete()

        cart_items = CartItem.objects.filter(user=user, is_deleted=False)
        totals = cart_items.aggregate(total_sum=Sum('total'))['total_sum'] or 0

        applied_coupon_id = request.session.get('applied_coupon_id')
        discounts = 0
        if applied_coupon_id:
            try:
                applied_coupon = Coupon.objects.get(id=applied_coupon_id, active=True,
                                                    active_date__lte=timezone.now(), expiry_date__gte=timezone.now())
                discounts = (totals * applied_coupon.discount) / 100
            except Coupon.DoesNotExist:
                request.session.pop('applied_coupon_id', None)

        cart_total = totals - discounts

        cart_count = cart_items.count()
        is_cart_empty = cart_items.count() == 0

        return JsonResponse({
            'success': True,
            'totals': totals,
            'discounts': discounts,
            'total': cart_total,
            'is_cart_empty': is_cart_empty,
            'cart_count': cart_count
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found in the cart'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

#======================================= user account ====================================================================================================================================
@cache_control(max_age=0,no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')



def user_account(request):
    user_address = Address.objects.filter(users=request.user)
    
    order_history = CartOrder.objects.filter(user=request.user).order_by('-id').annotate(product_name=Subquery(
        ProductOrder.objects.filter(order=OuterRef('pk')).order_by('id').values('product__product_name')[:1]
    ),
    product_image=Subquery(
        ProductOrder.objects.filter(order=OuterRef('pk')).order_by('id').values('product__productattribute__image')[:1]
    ))
    order_items = ProductOrder.objects.filter(user=request.user)
    for order in order_history:
        print(order.product_image)
    

    Wallet.objects.get_or_create(user=request.user)
    wallet = Wallet.objects.get(user=request.user)
    

    wallethistory =  WalletHistory.objects.filter(wallet=wallet).order_by('-created_at')
    for i in user_address:
        print(f'fasdfjasjfasl {i}')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account details have been updated successfully.')
            return redirect('indexuser:user_account')
        else:
            messages.error(request, 'Error updating account details. Please correct the errors below.')
    else:
        # Initialize the form with initial values from request.user
        form = UserProfileForm(instance=request.user)
    
    context={
        'user_address': user_address,
        'user_data': request.user,
        'order_history': order_history,
        'order_items': order_items,
        'wallet': wallet,
        'wallethistory': wallethistory,
        'form': form,
    }
    return render(request, 'userhome/user_account.html', context)



#========================== edit,delete address ==========================================================================================================================================================================
def add_address(request):
    if request.method=='POST':
        form = AddressForm(request.POST,request.FILES)
        if form.is_valid():
            address=form.save(commit=False)
            address.users = request.user
            address.save()
            return redirect('indexuser:user_account')
    else:
        form=AddressForm()
    context={
        'form':form
    }
    return render(request, 'userhome/add_address.html',context)

@login_required(login_url='user_login')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, users=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.instance.users = request.user
            form.save()
            return render(request,'userhome/user_account.html')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'userhome/edit_address.html', {'form': form, 'address': address})
    

@login_required(login_url='user_login')
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, users=request.user)
    
    if request.method == 'POST':
        address.delete()
        return redirect('user_account')
    
    return render(request, 'userhome/delete_address.html', {'address': address})
#==================================== order items that user order =============================================================================================================================================================
@login_required(login_url='user_login')
def order_items(request, order_number):
    order = CartOrder.objects.get(id = order_number)
    product_orders = ProductOrder.objects.filter(order=order)
    for item in product_orders:
        item.subtotal = item.product_price * item.quantity
    context = {
        'order': order,
        'product_orders': product_orders,
        'order_total': sum(item.subtotal for item in product_orders),
    }
    print(f'the ord{order.selected_address}')


    return render(request, 'userhome/user_order_history.html', context)



#============================= cancel and return order ========================================================================================================================================================================
@login_required(login_url='user_login')
def cancell(request,order_number):
    try:
        order = CartOrder.objects.get(id=order_number)
        wallet = Wallet.objects.get(user=request.user)

        if order.payment.payment_method == 'Wallet' or order.payment.payment_method == 'Razorpay':
            wallet.balance += order.order_total
            wallet.save()
            WalletHistory.objects.create(
                        wallet=wallet,
                        type='Credited',
                        amount=order.order_total,
                        reason='Item cancelation'
                        )

            refunded_message = f'Amount of {order.order_total} refunded successfully to your wallet.'
            messages.success(request, refunded_message)
    
            for product_order in order.productorder_set.all():
                product_attribute = product_order.variations
                product_attribute.stock += product_order.quantity
                product_attribute.save()

        order.status = 'Cancelled'
        order.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    except Exception as e:
        print(e)
       
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='user_login')
def return_order(request,order_number):
    try:
        order = CartOrder.objects.get(id=order_number)
        wallet = Wallet.objects.get(user=request.user)

        wallet.balance += order.order_total
        wallet.save()
        WalletHistory.objects.create(
                    wallet=wallet,
                    type='Credited',
                    amount=order.order_total
                    )

        refunded_message = f'Amount of {order.order_total} refunded successfully to your wallet.'
        messages.success(request, refunded_message)

        for product_order in order.productorder_set.all():
            product_attribute = product_order.variations
            product_attribute.stock += product_order.quantity
            product_attribute.save()

        order.status = 'Return'
        order.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    except CartOrder.DoesNotExist:
        pass

    except Wallet.DoesNotExist:
        pass

    except Exception as e:
        print(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

#================================ useraccount edit and save  ===========================================================================================================================================

def edit_user(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account details have been updated successfully.')
            return redirect('indexuser:user_account')
        else:
            messages.error(request, 'Error updating account details. Please correct the errors below.')
    else:
        # Initialize the form with initial values from user_data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserProfileForm(instance=request.user, initial=initial_data)
    
    return render(request, 'userhome/user_account.html', {'form': form})



#===========================================================wishlist=========================================================================

def wishlist(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Login to access wishlist')
        return redirect('user_login')
    else:
        context = {}
        try:
            wishlist_items = WishlistItem.objects.filter(user=request.user)
            context = {
                'wishlist_items': wishlist_items
            }
        except WishlistItem.DoesNotExist:
            pass
    return render(request, 'userhome/wishlist.html', context)

def add_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.info(request, 'Login to access wishlist')
        return redirect('signin')
    else:
        try:
            wishlist_item = WishlistItem.objects.get(user=request.user, product_id=product_id)
            messages.info(request, 'Product is already in your wishlist')
        except WishlistItem.DoesNotExist:
            WishlistItem.objects.create(user=request.user, product_id=product_id)
            messages.success(request, 'Product added to your wishlist successfully')
        
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def delete_wishlist(request, wishlist_item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_item_id, user=request.user)
    wishlist_item.delete()
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))



#========================================================return a product===========================================================
@login_required(login_url='user_login')
def return_order(request,order_number):
    try:
        order = CartOrder.objects.get(id=order_number)
        wallet = Wallet.objects.get(user=request.user)

        wallet.balance += order.order_total
        wallet.save()
        WalletHistory.objects.create(
                    wallet=wallet,
                    type='Credited',
                    amount=order.order_total,
                    reason='Return Order Item'
                    )

        refunded_message = f'Amount of {order.order_total} refunded successfully to your wallet.'
        messages.success(request, refunded_message)

        for product_order in order.productorder_set.all():
            product_attribute = product_order.variations
            product_attribute.stock += product_order.quantity
            product_attribute.save()

        order.status = 'Return'
        order.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    except CartOrder.DoesNotExist:
        pass

    except Wallet.DoesNotExist:
        pass

    except Exception as e:
        print(e)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
#======================================================search==================================================================
def search(request):
    q=request.GET['q']
    try:
        discount_offer = ProductOffer.objects.get(active=True)
    except ProductOffer.DoesNotExist:
        discount_offer = None
    if discount_offer:
        current_date = timezone.now()
        if current_date > discount_offer.end_date or current_date < discount_offer.start_date:
            discount_offer.active = False
            discount_offer.save()
    try:
        
        discounted_offer = CategoryOffer.objects.filter(active=True)
    except ProductOffer.DoesNotExist:
        discounted_offer = None
    if discounted_offer:
        for dis in discounted_offer:
            products_with_discount = Product.objects.filter(category=dis.category, is_available=True)
            current_date = timezone.now()
            if current_date > dis.end_date or current_date < dis.start_date:
                dis.active = False
                dis.save()
    data = Product.objects.filter(product_name__icontains=q).order_by('-id')
    return render(request,'userhome/search.html',{'data':data,"discount_offer":discount_offer,"discounted_offer":discounted_offer,})

#...........................popularity------------------------------------


def popularity(request):
    # Annotate each product with the count of orders and order them by count in descending order
    popular_products = Product.objects.annotate(order_count=Count('productorder')).order_by('-order_count')[:10]
    context = {'products': popular_products}
    
    return render(request, 'userhome/index.html', context)
