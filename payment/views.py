from django.shortcuts import render,redirect
from mileapp.models import *
from mileapp.views import *
from .models import *
from datetime import datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.conf import settings
import razorpay




#===========================================================================================================================================
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

#===========================================================cash on delivery===================================================================
@cache_control(no_cache=True, must_revalidate=True, no_store=True)    
@login_required(login_url='user_login')

def place_order(request):
    user = request.user 
    items = CartItem.objects.filter(user=user, is_deleted=False)
    request.session.get('applied_coupon_id', None)  
    request.session.get('totals', 0)
    total = request.session.get('total', 0)
    request.session.get('discounts', 0)
   

    user_addresses = items.first().address

    short_id = str(random.randint(1000, 9999))
    yr = datetime.now().year
    dt = int(datetime.today().strftime('%d'))
    mt = int(datetime.today().strftime('%m'))
    d = datetime(yr, mt, dt).date()
    payment_id = f"PAYMENT-{timezone.now().strftime('%Y%m%d%H%M%S')}"

    current_date = d.strftime("%Y%m%d")
    short_id = str(random.randint(1000, 9999))
    order_numbers = current_date + short_id 
    coupons = []

    for item in items:
        coupon = item.coupon
        coupons.append(coupon)

    if coupons:
        coupon = coupons[0]
    else:
        coupon = None

    var=CartOrder.objects.create(
        user=request.user,
        order_number=order_numbers,
        order_total= total,
        coupen=coupon,
        selected_address=user_addresses,
        ip=request.META.get('REMOTE_ADDR')    
    )
    var.save()
    payment_instance=Payments.objects.create(
        user=request.user,
        payment_id=payment_id,
        payment_method='COD',
        amount_paid= total,
        status='Pending',
                
    )
        
    var.payment=payment_instance
    var.save()
            
    cart=CartItem.objects.filter(user=request.user)
            
    for item in cart:
        orderedproduct=ProductOrder()
        item.product.stock-=item.quantity
        item.product.save()
        orderedproduct.order=var
        orderedproduct.payment=payment_instance
        orderedproduct.user=request.user
        orderedproduct.product=item.product.product
        orderedproduct.quantity=item.quantity
        orderedproduct.product_price=item.product.price
        product=item.product
        color=item.product.color 
        orderedproduct.variations = product
        orderedproduct.ordered=True
        orderedproduct.save()
        item.delete()  
    if 'applied_coupon_id' in request.session:
        request.session.pop('applied_coupon_id')     
    request.session.pop('totals')
    total = request.session.pop('total')
    request.session.pop('discounts')
      
    return redirect('pay:order_success')


#=================================================Wallet order placement =====================================================
def wallet_place_order(request):
    try:
        user = request.user
        items = CartItem.objects.filter(user=user, is_deleted=False)
        request.session.get('applied_coupon_id', None)  
        request.session.get('totals', 0)
        total = request.session.get('total', 0)
        request.session.get('discounts', 0)

        user_addresses = items[0].address
        coupons = [item.coupon for item in items]
        coupon = coupons[0] if coupons else None

        try:
            print('in the second try')
            wallet = Wallet.objects.get(user=request.user)
            if total <= wallet.balance:
                # Generate order number
                short_id = str(random.randint(1000, 9999))
                yr = datetime.now().year
                dt = int(datetime.today().strftime('%d'))
                mt = int(datetime.today().strftime('%m'))
                d = datetime(yr, mt, dt).date()
                current_date = d.strftime("%Y%m%d")
                order_numbers = current_date + short_id

                # Create CartOrder instance
                cart_order = CartOrder.objects.create(
                    user=request.user,
                    order_number=order_numbers,
                    order_total=total,
                    coupen=coupon,
                    selected_address=user_addresses,
                    ip=request.META.get('REMOTE_ADDR')
                )

                # Create Payment instance
                payment_instance = Payments.objects.create(
                    user=request.user,
                    payment_id=f"PAYMENT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    payment_method='Wallet', 
                    amount_paid=total,
                    status='paid',
                )
                print(f'the payment {payment}')
                # Assign Payment instance to CartOrder
                cart_order.payment = payment_instance
                cart_order.save()

                # Create ProductOrder instances
                for item in CartItem.objects.filter(user=request.user):
                    orderedproduct = ProductOrder()
                    item.product.stock -= item.quantity
                    item.product.save()
                    orderedproduct.order = cart_order
                    orderedproduct.payment = payment_instance
                    orderedproduct.user = request.user
                    orderedproduct.product = item.product.product
                    orderedproduct.quantity = item.quantity
                    orderedproduct.product_price = item.product.price
                    product_attribute = ProductAttribute.objects.get(product=item.product.product, color=item.product.color)
                    orderedproduct.variations = product_attribute
                    orderedproduct.ordered = True
                    orderedproduct.save()
                    print(f'the product for loop {item}')
                    item.delete()

                # Update wallet balance and create WalletHistory entry
                wallet.balance -= total
                wallet.save()

                WalletHistory.objects.create(
                    wallet=wallet,
                    type='Debit',
                    amount=total,
                    reason='Order Placement'
                )

                # Fetch wallet history in descending order of creation date
                

                # Clear session data
                request.session.pop('applied_coupon_id', None)   
                request.session.pop('totals', 0)
                request.session.pop('total', 0)
                request.session.pop('discounts', 0)

                return redirect('pay:order_success')

            else:
                messages.error(request, 'Wallet balance is less than the total amount')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        except Wallet.DoesNotExist:
            messages.error(request, 'Wallet not found for the user')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    except Exception as e:
        print(f"An error occurred: {e}")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

#===================================================checkout =================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from .models import CartItem, Address, Wallet
from .forms import AddressForm

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
# def checkout(request):
#     user = request.user 
#     items = CartItem.objects.filter(user=user, is_deleted=False)
#     user_addresses = Address.objects.filter(users=request.user)
    
#     address_form = AddressForm(request.POST or None)
#     cart = CartItem.objects.filter(user=request.user).first()
#     cartval = CartItem.objects.filter(user=request.user)
#     total = 0
#     for i in cartval:
#         total += i.get_subtotal()

#     # Fetch the wallet information
#     wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
    
#     if request.session.get('order_placed', False):
#         del request.session['order_placed']
#         return redirect('indexuser:user_index')  

#     if request.method == 'POST':
#         if 'use_existing_address' in request.POST:
#             selected_address_id = request.POST.get('existing_address')
#             selected_address = get_object_or_404(Address, id=selected_address_id)
#             return render(request, 'payment/payment.html', {
#                 'selected_address': selected_address,
#                 'items': items,
#                 'total': total - (cart.coupon.discount * 100)//2 if cart and cart.coupon else total,
#                 'wallet': wallet,  # Pass the wallet information to the payment page
#             })
        
#         elif address_form.is_valid():
#             address_instance = address_form.save(commit=False)
#             address_instance.users = request.user
#             address_instance.save()
#             CartItem.objects.filter(user=user, is_deleted=False).update(address=address_instance)
#             return render(request, 'payment/payment.html', {
#                 'new_address': address_instance,
#                 'items': items,
#                 'coupon': cart.coupon,
#                 'total': total - (cart.coupon.discount * 100)//2 if cart and cart.coupon else total,
#                 'cart_subtotal': total,
#                 'wallet': wallet,  # Pass the wallet information to the payment page
#             })

#     # Apply discount if cart has a coupon
#     if cart and cart.coupon:
#         total -= (cart.coupon.discount * 100)//2
    
#     return render(request, 'payment/checkout.html', {
#         'user_addresses': user_addresses,
#         'items': items,
#         'coupon': cart.coupon if cart else None,
#         'total': total - (cart.coupon.discount * 100)//2 if cart and cart.coupon else total,
#         'cart_subtotal': total,
#         'wallet': wallet,  # Pass the wallet information to the checkout page
#     })
def checkout(request):
    user = request.user 
    items = CartItem.objects.filter(user=user, is_deleted=False)
    user_addresses = Address.objects.filter(users=request.user)
    
    address_form = AddressForm(request.POST or None)
    totals = request.session.get('totals', 0)
    total = request.session.get('total', 0)
    discounts = request.session.get('discounts', 0)

    wallet = Wallet.objects.filter(user=user).first()
    wallet_balance = wallet.balance if wallet else 0

    wallet_button_disabled = total > wallet_balance
    wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0})

    if request.session.get('order_placed', False):
        del request.session['order_placed']
        return redirect('user_index')  

    if request.method == 'POST':
        if 'use_existing_address' in request.POST:
            selected_address_id = request.POST.get('existing_address')
            selected_address = get_object_or_404(Address, id=selected_address_id)
            # Update the address for all CartItems in the user's cart
            CartItem.objects.filter(user=user, is_deleted=False).update(address=selected_address.address)

            return render(request, 'payment/payment.html', {
                'selected_address': selected_address,
                'items': items,
                'total': total,
                'totals': totals,
                'discounts': discounts,
                'wallet_balance': wallet_balance,
                'wallet_button_disabled': wallet_button_disabled,
                'wallet':wallet,
                                        })
        
        elif address_form.is_valid():
            address_instance = address_form.save(commit=False)
            address_instance.users = request.user
            address_instance.save()
            CartItem.objects.filter(user=user, is_deleted=False).update(address=address_instance.address)
            return render(request, 'payment/payment.html', {
                'new_address': address_instance,
                'items': items,
                'total': total,
                'totals': totals,
                'discounts': discounts,
                'wallet_balance': wallet_balance,
                'wallet_button_disabled': wallet_button_disabled,
                'wallet': wallet,
            })
    
    return render(request, 'payment/checkout.html', {
        'user_addresses': user_addresses,
        'items': items,
        'total': total,
        'totals': totals,
        'discounts': discounts,
        'wallet': wallet, 
    })

#=========================================================payment with razorpay============================================================================
@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='user_login')
def payment(request):
    print("Entering payment")
    user=request.user 
    items=CartItem.objects.filter(user=user, is_deleted=False)
    user_addresses = Address.objects.filter(users=request.user)
    totals = request.session.get('totals', 0)
    total = request.session.get('total', 0)
    discounts = request.session.get('discounts', 0)

    if request.session.get('order_placed', False):
        del request.session['order_placed']
        return redirect('user_index')  


    if request.method == "POST":
        amount = request.POST.get('total', 0)
        amount = int(amount)
    
        currency = 'INR'
        amount_in_paise = amount
 
        razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paise,
                                                           currency=currency,
                                                           payment_capture='0'))
 
        razorpay_order_id = razorpay_order['id']
        callback_url = 'paymenthandler/'
 
        context = {
            'total': total,
            'items': items,
            'totals': totals,
            'discounts': discounts,
            'user_addresses': user_addresses,
        }
        context['razorpay_order_id'] = razorpay_order_id
        context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
        context['razorpay_amount'] = amount_in_paise
        context['currency'] = currency
        context['callback_url'] = callback_url
 
        return render(request, 'paymenthome/payment.html', context=context)

 #===============================================================================================================
@csrf_exempt
def paymenthandler(request):
    print("Wnt to join")
    user = request.user 
    items = CartItem.objects.filter(user=user, is_deleted=False)
    user_addresses = Address.objects.filter(users=request.user)
    total = items.aggregate(total_sum=Sum('total'))['total_sum']

    print(total,"totallllllllllll")

    if request.method == "POST":
        print(request.POST.dict())
        amount = request.POST.get('total')
        print(amount, "amount")

        try:

            payment_id = request.POST.get('razorpay_payment_id', '')
            print(payment_id,"paymentid")
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            print(razorpay_order_id,"razorpayid")
            signature = request.POST.get('razorpay_signature', '')
            print(signature,"signaturessss")

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,

            }

            if payment_id:
                print("Redirecting to order_success page")
                return redirect('pay:online_place_order')
            else:
                return render(request, 'payment/payment_failed.html')
        except Exception as e:
            print("Error in paymenthandler:", str(e))
            return render(request, 'payment/payment_failed.html')
    else:
        return HttpResponseBadRequest()

    
#==========================================================online order like razorpay=======================================================
def online_place_order(request):
    user = request.user 
    items = CartItem.objects.filter(user=user, is_deleted=False)
    request.session.get('applied_coupon_id', None)  
    request.session.get('totals', 0)
    total = request.session.get('total', 0)
    request.session.get('discounts', 0)

    
    user_addresses = items[0].address
   
    coupons = []

    for item in items:
        coupon = item.coupon
        coupons.append(coupon)

    if coupons:
        coupon = coupons[0]
    else:
        coupon = None
    
        
    short_id = str(random.randint(1000, 9999))
    yr = datetime.now().year
    dt = int(datetime.today().strftime('%d'))
    mt = int(datetime.today().strftime('%m'))
    d = datetime(yr, mt, dt).date()
    payment_id = f"PAYMENT-{timezone.now().strftime('%Y%m%d%H%M%S')}"

    current_date = d.strftime("%Y%m%d")
    short_id = str(random.randint(1000, 9999))
    order_numbers = current_date + short_id 

    var=CartOrder.objects.create(
        user=request.user,
        order_number=order_numbers,
        coupen=coupon,
        order_total= total,
        selected_address=user_addresses,
        ip=request.META.get('REMOTE_ADDR')    
        )
    var.save()
    payment_instance=Payments.objects.create(
        user=request.user,
        payment_id=payment_id,
        payment_method='Razorpay',
        amount_paid= total,
        status='paid',
                
        )
        
    var.payment=payment_instance
    var.save()
    cart=CartItem.objects.filter(user=request.user)
            
    for item in cart:
        orderedproduct=ProductOrder()
        item.product.stock-=item.quantity
        item.product.save()
        orderedproduct.order=var
        orderedproduct.payment=payment_instance
        orderedproduct.user=request.user
        orderedproduct.product=item.product.product
        orderedproduct.quantity=item.quantity
        orderedproduct.product_price=item.product.price
        product_attribute = ProductAttribute.objects.get(product=item.product.product, color=item.product.color)
        orderedproduct.variations = product_attribute
        orderedproduct.ordered=True
        orderedproduct.save()
        item.delete() 

    request.session.pop('applied_coupon_id', None)    
    request.session.pop('totals', 0)
    total = request.session.pop('total', 0)
    request.session.pop('discounts', 0) 

    return redirect('pay:order_success')
#===============================================order success=====================================================
@cache_control(no_cache=True, must_revalidate=True, no_store=True)    
@login_required(login_url='user_login')
def order_success(request):
    order = CartOrder.objects.filter(user=request.user).order_by('-id').first()
    print(order) 
    product_orders = ProductOrder.objects.filter(order=order)
    address = order.selected_address
    
    request.session['order_placed'] = True
    messages.success(request, 'Order Placed sucessfully')
    context = {
        'order':order,
        'order_number': order.order_number,
        'order_status': order.status,
        'product_orders': product_orders,
        'address':address
    }
    return render(request,'payment/orderdetail.html',context)

#===============================================================invoice==========================================================================================================

def invoice(request,order_id,total=0):
    try:
        order=CartOrder.objects.get(id=order_id)
        orders=ProductOrder.objects.filter(order=order)

    except:
        pass
    coupon = order.coupen
    grand_total = order.order_total
    for item in orders:
        item.subtotal=item.quantity * item.product_price
        total += item.subtotal
    context={
        'order':order,
        'orders':orders,
        'grand_total':grand_total,
        'coupon':coupon,
    }

    return render(request,'payment/invoice.html',context) 