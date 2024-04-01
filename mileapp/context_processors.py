from .models import *
from payment.models import CartItem
from mileapp.models import WishlistItem
def get_filter(request):
    cats=Product.objects.distinct().values('category__category_name','category__id')
    brands=Product.objects.distinct().values('brand__brand_name','brand__id')
    colors=ProductAttribute.objects.distinct().values('color__color_name','color__id','color__color_code')
    data = {
        'cats' : cats,
        'brands' : brands,
        'colors' : colors,
    }
    return data

def CartCount(request):
    cart = None
    if request.user.is_authenticated:
        cart = CartItem.objects.filter(user = request.user)
    return {'cartcount':cart.count()} if cart else {'cartcount':0}

def WishCount(request):
    wish = None
    if request.user.is_authenticated:
        wish = WishlistItem.objects.filter(user = request.user)
    return {'wishcount':wish.count()} if wish else {'wishcount':0}
    