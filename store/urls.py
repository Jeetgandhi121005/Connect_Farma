# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    
    # --- Consumer Paths ---
    path('consumer/signup/', views.consumer_signup_view, name='consumer_signup'),
    path('consumer/login/', views.consumer_login_view, name='consumer_login'),
    path('home/', views.consumer_home_view, name='consumer_home'),
    path('about/', views.about_us_view, name='about_us'),
    path('reviews/', views.reviews_view, name='reviews'),

    # --- Farmer Paths ---
    path('farmer/signup/', views.farmer_signup_view, name='farmer_signup'),
    path('farmer/login/', views.farmer_login_view, name='farmer_login'),
    path('farmer/dashboard/', views.farmer_dashboard_view, name='farmer_dashboard'),
    path('farmer/products/', views.farmer_products_view, name='farmer_products'),
    path('farmer/products/add/', views.farmer_add_product_view, name='farmer_add_product'),
    path('farmer/product/update/<int:product_id>/', views.update_product_view, name='update_product'),
    path('farmer/product/delete/<int:product_id>/', views.delete_product_view, name='delete_product'),
    path('farmer/orders/', views.farmer_orders_view, name='farmer_orders'),
    path('farmer/payments/', views.farmer_payments_view, name='farmer_payments'),
    path('farmer/order/complete/<int:order_id>/', views.complete_order_view, name='complete_order'),
    path('farmer/request-payout/', views.request_payout_view, name='request_payout'),
    path('farmer/collect-payment/', views.collect_payment_view, name='collect_payment'),
    # --- Cart & Order Paths ---
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/update/', views.update_cart_view, name='update_cart'),
    path('cart/checkout/', views.checkout_view, name='checkout_view'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),

    # --- General ---
    path('logout/', views.logout_view, name='logout'),
    
    # --- REMOVED 'set_location' URL ---
]