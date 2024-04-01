from django.urls import path,include
from .import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'pay'


urlpatterns = [
    path('checkout/',views.checkout,name='checkout'),
    path('payment/',views.payment,name="payment"),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
    path('place_order/',views.place_order,name="place_order"),
    path('order_success/', views.order_success, name='order_success'),
    path('online_place_order', views.online_place_order, name='online_place_order'),
    path('wallet_place_order', views.wallet_place_order, name='wallet_place_order'),
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),

    
    
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
