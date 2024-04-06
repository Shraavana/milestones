from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('',views.admin_login,name='admin_login'),
    path('admin_logout/',views.admin_logout,name='admin_logout'),
    path('admin_index/',views.admin_index,name='admin_index'),
    path('admin_category/',views.admin_category,name='admin_category'),
    path('admin_category_insert/',views.admin_category_insert,name='admin_category_insert'),
    path('admin_category_edit/<int:id>',views.admin_category_edit,name='admin_category_edit'),
    path('admin_delete_category/<int:id>/', views.admin_delete_category, name='admin_delete_category'),
    path('admin_brand/',views.admin_brand,name='admin_brand'), 
    path('admin_brand_insert/',views.admin_brand_insert,name='admin_brand_insert'),
    path('admin_brand_edit/<int:id>',views.admin_brand_edit,name='admin_brand_edit'),
    path('admin_color/',views.admin_color,name='admin_color'), 
    path('admin_color_insert/',views.admin_color_insert,name='admin_color_insert'),
    path('admin_color_edit/<int:id>',views.admin_color_edit,name='admin_color_edit'),
    path('admin_product/',views.admin_product,name='admin_product'),   
    path('admin_product_add/',views.admin_product_add,name='admin_product_add'),  
    path('admin_product_edit/<int:id>',views.admin_product_edit,name='admin_product_edit'),
    path('admin_product_delete/<int:id>',views.admin_product_delete,name='admin_product_delete'),
    path('admin_varient/',views.admin_varient,name='admin_varient'),  
    path('admin_varient_add/',views.admin_varient_add,name='admin_varient_add'), 
    path('admin_varient_edit/<int:id>',views.admin_varient_edit,name='admin_varient_edit'), 
    path('admin_varient_delete/<int:id>',views.admin_varient_delete,name='admin_varient_delete'), 
    path('customers/',views.customers,name='customers'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    

    path('admin_coupon/',views.admin_coupon,name='admin_coupon'),
    path('create_coupon/',views.create_coupon, name='create_coupon'),
    path('edit_coupon/<int:id>',views.edit_coupon,name='edit_coupon'),
    path('delete_coupon/<int:id>',views.delete_coupon,name='delete_coupon'),
    path('order/',views.order,name='order'),
    path('orderitems/<int:order_number>',views.order_items,name='orderitems'),
    path('cancel_order/<int:order_number>',views.cancell_order,name='cancell_order'),



    path('sales_report/',views.sales_report,name='sales_report'),
    path('product-offers/',views.product_offers, name='product-offers'),
    path('edit-product-offers/<int:id>',views.edit_product_offers, name='edit-product-offers'),
    path('create-product-offer/',views.create_product_offer, name='create-product-offer'),
    path('delete-product-offer/<int:id>/',views.delete_product_offer, name='delete-product-offer'),
    path('category-offers/',views.category_offers, name='category-offers'),
    path('edit-category-offers/<int:id>',views.edit_category_offers, name='edit-category-offers'), 
    path('create-category-offer/',views.create_category_offer, name='create-category-offer'),
    path('delete-category-offer/<int:id>/',views.delete_category_offer, name='delete-category-offer'),
    path('popular_products/',views.popular_products,name='popular_products'),
    path('popular_categories/',views.popular_categories,name='popular_categories'),
    
    

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)

