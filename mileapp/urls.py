
from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


app_name='indexuser'

urlpatterns = [
    path('',views.user_index,name='user_index'),
    path('user_login/',views.signin,name='user_login'),
    path('user_logout/',views.user_logout,name='user_logout'),
    path('sign_up/',views.signup,name='sign_up'),
    path('enter_otp/',views.enter_otp,name='enter_otp'),
    path('resend_otp/',views.resend_otp,name='resend_otp'),
    path('shop/', views.shop, name='shop'),
    path('shop/<int:category_id>', views.shop, name='products_by_category'),
    path('shop/<int:brand_id>/', views.shop, name='products_by_brand'),
    path('details/<int:category_id>/<int:product_id>', views.product_details, name='product_details'),
    path('details/<int:product_id>', views.product_details, name='product_details'),

    path('add_to_cart/',views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_list, name='cart'),
    path('update_qty',views.qty_update,name='update_qty'),
    path('delete_cart_item/', views.delete_cart_item, name='delete_cart_item'),
    path('remove_coupon/',views.remove_coupon, name='remove_coupon'),



    path('user_account/', views.user_account, name='user_account'),
    path('edit_user/',views.edit_user,name='edit_user'),
    path('change_password/',views.change_password,name='change_password'),

    path('order_items/<int:order_number>/', views.order_items, name='order_items'),
    path('add_address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('cancell/<int:order_number>/',views.cancell,name='cancell'),
    path('return_order/<int:order_number>/',views.return_order,name='return_order'),
    

    path('shop_des_price/',views.shop_des_price,name='shop_des_price'),
    path('shop_ase_price/',views.shop_ase_price,name='shop_ase_price'),
    path('shop0/',views.shop0,name='shop0'),
    path('shop1/',views.shop1,name='shop1'),


    path('wishlist',views.wishlist,name='wishlist'),
    path('add_wishlist/<int:product_id>/',views.add_wishlist,name='add_wishlist'),
    path('delete_wishlist/<int:wishlist_item_id>/',views.delete_wishlist,name='delete_wishlist'),



    path('search/',views.search,name='search'),
    path('popularity/',views.popularity,name='popularity'),
    


    
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
# i dont know user account is sufficient or not