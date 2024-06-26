from django.shortcuts import render,redirect
from mileapp.models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout
from django.shortcuts import get_object_or_404
from mileapp.forms import *
from django.contrib.auth.decorators import login_required
from adminhome.models import Coupon
from django.views.decorators.cache import cache_control,never_cache
from .forms import OrderForm,ProductOfferForm,CategoryOfferForm
from django.db import transaction
from adminhome.models import *
from payment.models import *
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate,TruncMonth, TruncYear
from django.db.models import Count,Sum
from django.utils.timezone import make_aware
from mileapp.models import category
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from decimal import Decimal
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseBadRequest



#=======================================admin login=================================================================================================================================
@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user=authenticate(request, email=email,password=password)
        if user is not None and user.is_active and user.is_superadmin and user.is_staff and user.is_admin :
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('admin_index')
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'adminhome/adminlogin.html')
    return render(request, 'adminhome/adminlogin.html')

def admin_logout(request):
    logout(request)
    return render(request,'adminhome/adminlogin.html')

#===================================================admin index page==================================================================================================================
@never_cache
@login_required(login_url='admin_login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_index(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
 
    product_count=Product.objects.count()
    category_count=category.objects.count()
    orders=CartOrder.objects.all()
    last_orders= CartOrder.objects.order_by('-created_at')[:5]
    orders_count=orders.count()
    total_users_count = User.objects.count()
    total = 0
    inte_revenue=0
    for order in orders:
        if order.status == 'Delivered':
            total += order.order_total
            
        if (order.payment and order.payment.payment_method == 'Razorpay' and order.status != 'Cancelled' ) or (order.payment and order.payment.payment_method == 'Wallet' and order.status != 'Cancelled'):
            total += order.order_total
    revenue=int(total)
    inte_revenue = orders.aggregate(total_revenue=Sum('order_total'))['total_revenue'] or 0
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    print('Start Date:', start_date)
    print('End Date:', end_date)
    revenue = orders.aggregate(total_revenue=Sum('order_total'))['total_revenue'] or 0
    daily_order_counts = (
            CartOrder.objects
            .filter(created_at__range=(start_date, end_date))
            .values('created_at')
            .annotate(order_count=Count('id'))
            .order_by('created_at')
        )
    print(f'daily orrderr {daily_order_counts}')
    print('SQL Query:', daily_order_counts.query)
    dates = [entry['created_at'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]
    print('Daily Chart Data:')
    print('Dates:', [entry['created_at'] for entry in daily_order_counts])
    print('Counts:', [entry['order_count'] for entry in daily_order_counts])
    print(dates)
    print(counts)


    end_date = timezone.now()
    start_date = end_date - timedelta(days=365) 
    
    monthly_order_counts = (
        CartOrder.objects
        .filter(created_at__range=(start_date, end_date))   
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(order_count=Count('id'))
        .order_by('month')
    )
    monthlyDates = [entry['month'].strftime('%Y-%m') for entry in monthly_order_counts]
    monthlyCounts = [entry['order_count'] for entry in monthly_order_counts]
    
    yearly_order_counts = (
        CartOrder.objects
        .annotate(year=TruncYear('created_at'))
        .values('year')
        .annotate(order_count=Count('id'))
        .order_by('year')
    )
    yearlyDates = [entry['year'].strftime('%Y') for entry in yearly_order_counts]
    yearlyCounts = [entry['order_count'] for entry in yearly_order_counts]

    statuses = ['Delivered','Paid','Pending', 'New', 'Conformed', 'Cancelled', 'Return','Shipped']
    order_counts = [CartOrder.objects.filter(status=status).count() for status in statuses]

    context={
        'product_count':product_count,
        'category_count':category_count,
        'orders_count':orders_count,
        'dates': dates,
        'counts': counts,
        'monthlyDates':monthlyDates,
        'monthlyCounts':monthlyCounts,
        'yearlyDates':yearlyDates,
        'yearlyCounts':yearlyCounts,
        'last_orders': last_orders,
        'revenue':revenue,
        'total_users_count': total_users_count,
        'statuses': statuses,
        'order_counts': order_counts,
        'inte_revenue':inte_revenue,
    }
    return render(request, 'adminhome/adminindex.html', context)

#================================================admin add new,edit category====================================================================================================================

@login_required(login_url='admin_login')
def admin_category_insert(request):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        new_cat = category(category_name=category_name)
        new_cat.save()
        return redirect('admin_category')
    return render(request,'adminhome/category.html')

@login_required(login_url='admin_login')
def admin_category_edit(request,id):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        slug = request.POST.get('slug')
        edit=category.objects.get(id=id)
        edit.category_name = category_name
        edit.slug = slug
        edit.save()
        return redirect('admin_category')
    obj = category.objects.get(id=id)
    context = {
        "obj":obj
    }
    return render(request,'adminhome/category_edit.html', context)

#=============================================== Brand list,add,edit =============================================================================================================

@login_required(login_url='admin_login')
def admin_brand(request):
    data=Brand.objects.all()
    context={
        'data':data
    }
    return render(request, 'adminhome/brand.html', context)

@login_required(login_url='admin_login')
def admin_brand_insert(request):
    if request.method == 'POST':
        brand_name = request.POST.get('name')
        new_cat = Brand(brand_name=brand_name)
        new_cat.save()
        return redirect('admin_brand')
    return render(request,'adminhome/brand.html')

@login_required(login_url='admin_login')
def admin_brand_edit(request,id):
    if request.method == 'POST':
        brand_name = request.POST.get('name')
        edit=Brand.objects.get(id=id)
        edit.brand_name = brand_name
        edit.save()
        return redirect('admin_brand')
    obj = Brand.objects.get(id=id)
    context = {
        "obj":obj
    }
    return render(request,'adminhome/brand_edit.html', context)



@login_required(login_url='admin_login')
def brand_available(request, brand_id):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    brand = get_object_or_404(Brand, id=brand_id)
    
    if brand.is_active:
        brand.is_active=False
       
    else:
        brand.is_active=True
    brand.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


#=================================================== color list, add, edit ==========================================================================================================

@login_required(login_url='admin_login')
def admin_color(request):
    data=Color.objects.all()
    context={
        'data':data
    }
    return render(request, 'adminhome/color.html', context)

@login_required(login_url='admin_login')
def admin_color_insert(request):
    if request.method == 'POST':
        color_name = request.POST.get('name')
        color_code = request.POST.get('code')
        new_cat = Color(color_name=color_name,color_code=color_code)
        new_cat.save()
        return redirect('admin_color')
    return render(request,'adminhome/color.html')

@login_required(login_url='admin_login')
def admin_color_edit(request,id):
    if request.method == 'POST':
        color_name = request.POST.get('name')
        color_code = request.POST.get('code')
        edit=Color.objects.get(id=id)
        edit.color_name = color_name
        edit.color_code = color_code
        edit.save()
        return redirect('admin_color')
    obj = Color.objects.get(id=id)
    context = {
        "obj":obj
    }
    return render(request,'adminhome/color_edit.html', context)

#=========================================== admin add, list, edit, delete product =========================================================================================================

@login_required(login_url='admin_login')
def admin_product(request):
    item = Product.objects.all()
    context = {
        "item":item
    }
    print(item)
    return render(request,'adminhome/product.html', context)

@login_required(login_url='admin_login')
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            product=form.save(commit=False)
            product.save()
            images=request.FILES.getlist('images')
            for img in images:
                ProductImages.objects.create(product=product,images=img)
            return redirect('admin_product')
    else:
        form = ProductForm()    

    brands = Brand.objects.all()
    categories = category.objects.all()

    context = {
        'brands': brands,
        'categories': categories,
        'form' : form,
    }
    return render(request,'adminhome/product_add.html',context)

@login_required(login_url='admin_login')
def admin_product_edit(request, id):
    product = get_object_or_404(Product, id=id)
    images = product.product_image.all()
    brands = Brand.objects.all()
    categories = category.objects.all()

    if request.method == 'POST':
        product_form = ProductForm(request.POST, instance=product)
        images_form = ProductImagesForm(request.POST, request.FILES)

        # Check if the delete_image checkboxes are checked for any existing images
        for img in images:
            if f'delete_image_{img.id}' in request.POST:
                img.delete()

        # Continue with the product update logic
        if product_form.is_valid() and images_form.is_valid():
            product_form.save()

            # Save the images form separately to handle new images
            images_form.save()
            return redirect('admin_product')

    else:
        product_form = ProductForm(instance=product)
        images_form = ProductImagesForm()

    context = {
        'product': product,
        'brands': brands,
        'categories': categories,
        'images': images,
        'product_form': product_form,
        'images_form': images_form,
    }

    return render(request, 'adminhome/product_edit.html', context)
@login_required(login_url='admin_login')
def admin_product_delete(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        product.delete()
        return redirect('admin_product')

    context = {'product': product}
    return render(request, 'adminhome/product_delete.html', context)
    
#=====================================varient list, add, edit===============================================================================================================================================================
@login_required(login_url='admin_login')
def admin_varient(request):
    cat=category.objects.all()
    item = ProductAttribute.objects.filter(is_deleted=False)
    context = {
        "item":item,
        "cat":cat
    }
    return render(request,'adminhome/varient.html', context)

@login_required(login_url='admin_login')
def admin_varient_add(request):
    if request.method == 'POST':
        form = ProductAttributeForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            return redirect('admin_varient')
    else:
        form = ProductAttributeForm()    

    brands = Brand.objects.all()
    categories = category.objects.all()

    context = {
        'brands': brands,
        'categories': categories,
        'form' : form,
    }
    return render(request, 'adminhome/varient_add.html', context)

@login_required(login_url='admin_login')
def admin_varient_edit(request, id):
    product = get_object_or_404(ProductAttribute, id=id)

    if request.method == 'POST':
        product_form = ProductAttributeForm(request.POST, request.FILES, instance=product)
        if product_form.is_valid():
            product_form.save()
            messages.success(request, 'Updated sucessfully')
            return redirect('admin_varient')

    else:
        product_form = ProductAttributeForm(instance=product)

    context = {
        'product_form': product_form,
        'product': product,
    }

    return render(request, 'adminhome/varient_edit.html', context)
@login_required(login_url='admin_login')
def admin_varient_delete(request, id):
    product = get_object_or_404(ProductAttribute, id=id)

    if request.method == 'POST':
        product.delete()
        return redirect('admin_varient')

    context = {'product': product}
    return render(request, 'adminhome/product_delete.html', context)

#==================================================admin can view the customers list======================================================================================================================================

@login_required(login_url='admin_login')
def customers(request):
    user = User.objects.all()
    context = {
        'user':user
    }
    return render(request, 'adminhome/customers.html',context)


#================================================== admin can block and unblock the user =======================================================================================================
  
@login_required(login_url='admin_login')
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Toggle the is_active field
    user.is_active = not user.is_active
    user.save()

    messages.success(request, f'{user.username} has been {"blocked" if not user.is_active else "unblocked"}.')

    return redirect('customers')

#=========================================================admin coupon========================================
@login_required(login_url='admin_login')
def admin_coupon(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    coupon = Coupon.objects.all()
    return render(request, 'adminhome/admin_coupon.html',{'coupon':coupon})

#=================================================create coupon==================================================================

@login_required(login_url='admin_login')
def create_coupon(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    if request.method == 'POST':
        code = request.POST['code']
        discount = float(request.POST['discount'])
        active = request.POST.get('active') == 'on'
        active_date = timezone.now().date()  # Get the current date
        expiry_date = request.POST['expiry_date']

        # Validate active date
        if active_date > timezone.datetime.strptime(expiry_date, '%Y-%m-%d').date():
            messages.warning(request, 'Active date should not be greater than expiry date')
            return render(request, 'adminhome/create_coupon.html')

        # Validate coupon code
        if len(code.strip()) < 3:
            messages.warning(request, 'Coupon code must be at least 3 characters long')
            return render(request, 'adminhome/create_coupon.html')

        # Validate discount percentage
        # Validate discount percentage
        if discount <= 2 or discount >= 90:
            messages.warning(request, 'Discount must be greater than 2% and less than 90%')
            return render(request, 'adminhome/create_coupon.html')


        # Check if coupon code already exists
        if Coupon.objects.filter(code=code).exists():
            messages.warning(request, f'Coupon with code {code} already exists')
            return render(request, 'adminhome/create_coupon.html')

        coupon = Coupon(
            code=code,
            discount=discount,
            active=active,
            active_date=active_date,
            expiry_date=expiry_date
        )
        coupon.save()
        messages.success(request, 'Coupon created successfully')
        return redirect('admin_coupon')

    return render(request, 'adminhome/create_coupon.html')


@login_required(login_url='admin_login')
def edit_coupon(request, id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    coupon_code = get_object_or_404(Coupon, id=id)
    
    if request.method == 'POST':
        code = request.POST['code']
        discount = float(request.POST['discount'])
        active = request.POST.get('active') == 'on'
        active_date = request.POST['active_date']
        expiry_date = request.POST['expiry_date']
        
        # Validate active date
        if active_date > expiry_date:
            messages.warning(request, 'Active date should not be greater than expiry date')
            return render(request, 'adminhome/update_coupon.html', {'coupon_code': coupon_code})
        
        # Validate coupon code length
        if len(code.strip()) < 3:
            messages.warning(request, 'Coupon code must be at least 3 characters long')
            return render(request, 'adminhome/update_coupon.html', {'coupon_code': coupon_code})

        # Validate discount percentage
        if discount <= 2 or discount >= 90:
            messages.warning(request, 'Discount must be greater than 2% and less than 90%')
            return render(request, 'adminhome/update_coupon.html', {'coupon_code': coupon_code})

        # Check if coupon code already exists (excluding the current coupon being edited)
        if Coupon.objects.exclude(id=id).filter(code=code).exists():
            messages.warning(request, f'Coupon with code {code} already exists')
            return render(request, 'adminhome/update_coupon.html', {'coupon_code': coupon_code})

        coupon_code.code = code
        coupon_code.discount = discount
        coupon_code.active_date = active_date
        coupon_code.expiry_date = expiry_date
        coupon_code.active = active
        coupon_code.save()
        messages.success(request, 'Coupon updated successfully')
        return redirect('admin_coupon')
    
    return render(request, 'adminhome/update_coupon.html', {'coupon_code': coupon_code})


@login_required(login_url='admin_login')        
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_coupon(request,id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    try:
        coupon= get_object_or_404(Coupon, id=id)
        coupon.delete()
        messages.warning(request,"Coupon has been deleted successfully")
    except ValueError:
        return redirect('admin_coupon')


    return redirect('admin_coupon')  

#===========================================================order management=====================================================
@login_required(login_url='admin_login')
def order(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    status='all'
    order = CartOrder.objects.order_by('-created_at')
    form = OrderForm(request.POST or None)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            if status != 'all':
                order = order.filter(status=status)

    context = {
        'order':order,
        'form':form,
        'status':status
    }
    return render(request, 'adminhome/order.html',context)
#=============================================================order items====================================================================

@login_required(login_url='admin_login')
def order_items(request, order_number):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    try:
        order = CartOrder.objects.get(id=order_number)
    except Exception as e:
        print(e)

    order_items = ProductOrder.objects.filter(order=order)
    address = order.selected_address
    payment = Payments.objects.all()
    
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            if form.cleaned_data['status'] == 'Cancelled':
                cancell_order(request, order_number)
                return redirect('order')
            else:
                form.save()
                return redirect('orderitems', order_number=order.pk)
        else:
            messages.error(request, "Choose a valid status")
            return redirect('orderitems', order_number=order.pk)

    form = OrderForm(instance=order)

    context = {
        'order': order,
        'address': address,
        'order_items': order_items,
        'form': form,
        'payment': payment,
        
    }
    return render(request, 'adminhome/order_items.html', context)

#=========================================================order cancel==============================================
@login_required(login_url='admin_login')
def cancell_order(request, order_number):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    try:
        order = CartOrder.objects.get(id=order_number)
    except CartOrder.DoesNotExist:
        messages.error(request, f"Order with ID {order_number} does not exist.")
        return redirect('order')

    if order.status == 'Cancelled':
        messages.warning(request, f"Order with ID {order_number} is already cancelled.")
    else:
        order.status = 'Cancelled'
        order.save()

        allowed_payment_methods = ['Razorpay', 'Wallet']

        if order.payment.payment_method in allowed_payment_methods:
            with transaction.atomic():
                user_wallet = order.user.wallet if hasattr(order.user, 'wallet') else None

                if order.payment.payment_method == 'Razorpay':
                    if user_wallet:
                        user_wallet.balance += order.order_total
                        user_wallet.save()

                        WalletHistory.objects.create(
                            wallet=user_wallet,
                            type='Credited',
                            amount=order.order_total,
                            created_at=timezone.now(),
                            reason='Admin Cancellation'
                        )
                elif order.payment.payment_method == 'Wallet':
                    if user_wallet:
                        user_wallet.balance += order.order_total
                        user_wallet.save()

                        WalletHistory.objects.create(
                            wallet=user_wallet,
                            type='Credited',
                            amount=order.order_total,
                            created_at=timezone.now(),
                            reason='Admin Cancellation'
                        )

                for order_item in order.productorder_set.all():
                    product_attribute = order_item.variations
                    product_attribute.stock += order_item.quantity
                    product_attribute.save()

        messages.success(request, f"Order with ID {order_number} has been cancelled successfully.")

    return redirect('order')
#==================================================admin view the category========================================================================================================

@login_required(login_url='admin_login')
def admin_category(request):
    data=category.objects.all()
    context={
        'data':data
    }
    return render(request, 'adminhome/category.html', context)
#===========================================================admin category=======================================================================
@login_required(login_url='admin_login')
def admin_delete_category(request, id):
    category_to_delete = get_object_or_404(category, id=id)
    category_to_delete.is_deleted = True
    category_to_delete.save()
    return redirect('admin_category')
#==================================================================================================================================================

@login_required(login_url='admin_login')
def admin_category_edit(request,id):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        edit=category.objects.get(id=id)
        edit.category_name = category_name
        edit.save()
        return redirect('admin_category')
    obj = category.objects.get(id=id)
    context = {
        "obj":obj
    }
    return render(request,'adminhome/category_edit.html', context)
#=============================================sales_Report==============================================================

@login_required(login_url='admin_login')



def sales_report(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    start_date_value = ""
    end_date_value = ""
    total_revenue = 0
    total_orders_count = 0
    product_count=Product.objects.count()
    
    try:
        orders = CartOrder.objects.filter(is_ordered=True).order_by('-created_at')
    except:
        pass
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date_value = start_date
        end_date_value = end_date
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Make start_date and end_date timezone aware
            start_date = timezone.make_aware(start_date)
            end_date = timezone.make_aware(end_date)
            
            # Check if start_date is a future date
            if start_date > timezone.now():
                messages.error(request, "Invalid start date. Please choose a past or present date.")
                return redirect('sales_report')
            
            # Check if end_date is the current date or earlier
            if end_date > timezone.now():
                messages.error(request, "Invalid end date. Please choose the current date or an earlier date.")
                return redirect('sales_report')
            
            orders = orders.filter(created_at__range=(start_date, end_date))
    
    # Calculate total revenue
    total_revenue = orders.aggregate(total_revenue=Sum('order_total'))['total_revenue'] or 0
    
    # Calculate total number of orders
    total_orders_count = orders.count()
    
    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    try:
        orders = paginator.page(page_number)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'start_date_value': start_date_value,
        'end_date_value': end_date_value,
        'total_revenue': total_revenue,
        'total_orders_count': total_orders_count,
        'product_count':product_count,
    }

    return render(request, 'adminhome/sales_report.html', context)


#============================================= add and delete the product offer ==================================================================================================================================================================
@login_required(login_url='admin_login')
def product_offers(request):
    offers=ProductOffer.objects.all()
    try:
        product_offer = ProductOffer.objects.get(active=True)
        print(product_offer)
    except ProductOffer.DoesNotExist:
        product_offer = None
    products = ProductAttribute.objects.all()
    for p in products:
        if product_offer:
            discounted_price = p.price - int(p.price * product_offer.discount_percentage / 100)
            p.price = int(max(discounted_price, int('0'))  )
        else:          
            p.price = p.price
        p.save()
    context={
        'offers':offers
    }
    return render(request, 'adminhome/product_offers.html',context)

@login_required(login_url='admin_login')
def edit_product_offers(request, id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    offer_discount = get_object_or_404(ProductOffer, id=id)
    print(f'Active Date: {offer_discount.start_date}')
    if request.method == 'POST':
        discount = request.POST['discount']
        active = request.POST.get('active') == 'on'
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        
        if end_date and start_date and end_date < start_date:
            messages.error(request, 'Expiry date must not be less than the start date.')
        else:
            start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))

            current_date = timezone.now()
            if start_date and end_date and (current_date < start_date or current_date > end_date):
                active = False
                messages.error(request, 'Offer cannot be activated now. Check the start date.')
           
            active_category_offer = CategoryOffer.objects.filter(active=True).first()

            if active_category_offer:
        
                messages.error(request, 'Cannot create/update product offer when a category offer is active.')
                return redirect('product-offers')

            if active:
                ProductOffer.objects.exclude(id=offer_discount.id).update(active=False)

            offer_discount.discount_percentage =  int(discount)
            offer_discount.start_date = start_date or None
            offer_discount.end_date = end_date or None
            offer_discount.active = active
            offer_discount.save()

            messages.success(request, 'Offer Updated successfully')
            return redirect('product-offers')
    
    return render(request, 'adminhome/edit_product_offers.html', {'offer_discount': offer_discount})
        
@login_required(login_url='admin_login')
def create_product_offer(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            discount_percentage = form.cleaned_data['discount_percentage']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            active = form.cleaned_data['active']
            
            if end_date and start_date and end_date < start_date:
                messages.error(request, 'Expiry date must not be less than the start date.')
            else:
                current_date = timezone.now()
                if start_date and end_date and (current_date < start_date or current_date > end_date):
                    active = False
                    messages.error(request, 'Offer cannot be activated now. Check the start date.')

                if active:
                    ProductOffer.objects.update(active=False)

                if discount_percentage or start_date or end_date or active:
                    form.save()
            
            return redirect('product-offers')  
    else:
        form = ProductOfferForm()

    return render(request, 'adminhome/create-product-offers.html', {'form': form})

@login_required(login_url='admin_login')
def delete_product_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    try:
        offer= ProductOffer.objects.get(id=id)
        product = ProductAttribute.objects.filter()
        for i in product:
            i.price = i.old_price
            i.save()
    except ValueError:
        return redirect('product-offers')
    offer.delete()
    messages.warning(request,"Offer has been deleted successfully")
    return redirect('product-offers')

@login_required(login_url='admin_login')
def category_offers(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    offers = CategoryOffer.objects.all()
    categories = category.objects.all()

    for cate in categories:
        try:
            category_offer = CategoryOffer.objects.filter(category=cate, active=True)
            print(category_offer)
        except CategoryOffer.DoesNotExist:
            category_offer = None
        products = ProductAttribute.objects.filter(product__category=cate, is_available=True)
        print(products)
        
        for product in products:
            if category_offer:
                for cat in category_offer:
                    discounted_price = product.old_price - (product.old_price * cat.discount_percentage / 100)
                    product.price = max(discounted_price, Decimal('0.00'))  
            else:
                product.price=product.old_price
            product.save()
    context = {
        'offers': offers
    }
    return render(request, 'adminhome/category_offers.html', context)

@login_required(login_url='admin_login')
def edit_category_offers(request, id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    offer_discount = get_object_or_404(CategoryOffer, id=id)
    print(f'Active Date: {offer_discount.start_date}')

    if request.method == 'POST':
        discount = request.POST.get('discount')
        active = request.POST.get('active') == 'on'
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if end_date and start_date:
            end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))

            if end_date < start_date:
                messages.error(request, 'Expiry date must not be less than the start date.')
                return redirect('edit-category-offers', id=id)
   
            current_date = timezone.now()
            if start_date and end_date and (current_date < start_date or current_date > end_date):
                active = False
                messages.error(request, 'Offer cannot be activated now. Check the start date.')

        active_product_offer = ProductOffer.objects.filter(active=True).first()

        if active_product_offer:
            
            messages.error(request, 'Cannot activate category offer when a product offer is active.')
            return redirect('category-offers')
        
        if active:
            CategoryOffer.objects.exclude(id=offer_discount.id).update(active=False)

        offer_discount.discount_percentage = discount or None
        offer_discount.start_date = start_date or None
        offer_discount.end_date = end_date or None
        offer_discount.active = active
        offer_discount.save()

        messages.success(request, 'Offer updated successfully')
        return redirect('category-offers')
    return render(request,'adminhome/edit_category_offers.html', {'offer_discount': offer_discount})

@login_required(login_url='admin_login')
def create_category_offer(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            discount_percentage = form.cleaned_data['discount_percentage']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            active = form.cleaned_data['active']

            if end_date and start_date and end_date < start_date:
                messages.error(request, 'Expiry date must not be less than the start date.')
            else:
               
                if active and CategoryOffer.objects.filter(category=category, active=True).exists():
                    messages.error(request, 'An active offer already exists for this category.')
                   
                else:
                    current_date = timezone.now()
                    if start_date and end_date and (current_date < start_date or current_date > end_date):
                        active = False
                        messages.error(request, 'Offer cannot be activated now. Check on start date')   
                    if active:
                        CategoryOffer.objects.update(active=False)
                    if discount_percentage or start_date or end_date or active:
                        form.save()
                    return redirect('category-offers')  
    else:
        form = CategoryOfferForm()
    return render(request, 'adminhome/create_category_offer.html', {'form': form})

@login_required(login_url='admin_login')
def delete_category_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    try:
        offer= get_object_or_404(CategoryOffer, id=id)
    except ValueError:
        return redirect('category-offers')
    offer.delete()
    messages.warning(request,"Offer has been deleted successfully")

    return redirect('category-offers')

#-----------------------------------------------------best seller products-----------------------------------------------------------

def popular_products(request):
    # Annotate each product with the count of orders and order them by count in descending order
    popular_products = Product.objects.annotate(order_count=Count('productorder')).order_by('-order_count')[:3]
    context = {'products': popular_products}
    
    return render(request, 'adminhome/popular_products.html', context)




def popular_categories(request):
    # Annotate each category with the count of orders for products in that category
    best_seller_categories = category.objects.annotate(order_count=Count('product__productorder')).order_by('-order_count')[:2]
    
    context = {'products': best_seller_categories}
    
    return render(request, 'adminhome/popular_categories.html', context)

############################################################THE END################################################################################