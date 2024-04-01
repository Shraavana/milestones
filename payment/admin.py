from django.contrib import admin
from .models import CartItem, CartOrder,Transaction

# Register your models here.

admin.site.register(CartItem)
admin.site.register(CartOrder)
admin.site.register(Transaction)
