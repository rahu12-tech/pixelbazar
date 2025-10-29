from django.urls import path
from . import views
from .debug_views import debug_products

urlpatterns = [
    # Auth APIs
    path('signup/', views.signup, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    
    # User APIs
    path('user/profile/', views.get_user_profile, name='get_user_profile'),
    path('profile/', views.get_user_profile, name='get_profile'),
    path('profile/update/', views.update_user_profile, name='update_profile'),
    path('auth/refresh/', views.refresh_token, name='refresh_token'),
    
    # Product APIs
    path('products/', views.get_products, name='get_products'),
    path('products/<int:product_id>/', views.get_product_detail, name='get_product_detail'),
    path('products/search/', views.search_products, name='search_products'),
    
    # Cart APIs
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/<int:cart_id>/update/', views.update_cart, name='update_cart'),
    path('cart/<int:cart_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Wishlist APIs
    path('wishlist/', views.get_wishlist, name='get_wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/<int:wishlist_id>/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('api/wishlist/', views.get_wishlist, name='api_get_wishlist'),
    path('api/wishlist/add/', views.add_to_wishlist, name='api_add_to_wishlist'),
    path('api/wishlist/<int:wishlist_id>/remove/', views.remove_from_wishlist, name='api_remove_from_wishlist'),
    
    # Address APIs
    path('addresses/', views.get_addresses, name='get_addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/<int:address_id>/update/', views.update_address, name='update_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    
    # Checkout & Payment APIs
    path('checkout/create-order/', views.create_order, name='create_order'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    
    # Order APIs
    path('orders/', views.get_order_history, name='get_order_history'),
    path('get-orders/', views.get_orders, name='get_orders'),
    path('orders/<str:order_id>/', views.get_order_detail, name='get_order_detail'),
    path('orders/<str:order_id>/track/', views.track_order, name='track_order'),
    path('orders/<str:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<str:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('orders/<str:order_id>/success/', views.get_payment_success_details, name='get_payment_success_details'),
    
    # Return & Refund APIs
    path('orders/<str:order_id>/return/', views.request_return, name='request_return'),
    path('returns/<str:return_id>/status/', views.get_return_status, name='get_return_status'),
    
    # Legacy endpoints for backward compatibility
    path('addtocart', views.legacy_add_to_cart, name='legacy_add_to_cart'),
    
    # Additional Cart APIs
    path('cart/update/', views.cart_update_api, name='cart_update_api'),
    path('cart/remove/', views.cart_remove_api, name='cart_remove_api'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Frontend Order APIs
    path('order/', views.create_order_api, name='create_order_api'),
    path('check-pincode/', views.check_pincode, name='check_pincode'),
    path('create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    
    # Admin APIs
    path('admin/orders/<str:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Debug APIs
    path('debug/products/', debug_products, name='debug_products'),
    
    # Coupon & Gift Card APIs
    path('coupons/', views.get_coupons, name='get_coupons'),
    path('coupons/apply/', views.apply_coupon, name='apply_coupon'),
    path('gift-cards/', views.get_gift_cards, name='get_gift_cards'),
    
    # Music Banner & Category APIs
    path('music-banner/', views.get_music_banner, name='get_music_banner'),
    path('products/category/<str:category>/', views.get_products_by_category, name='get_products_by_category'),
    
    # Category Management APIs
    path('categories/', views.get_categories, name='get_categories'),
    path('categories/add/', views.add_category, name='add_category'),
    
    # Contact APIs
    path('contact/', views.submit_contact, name='submit_contact'),
    path('contacts/', views.get_contacts, name='get_contacts'),
    
    # Simple Cart endpoint for frontend
    path('cart/', views.get_cart, name='simple_cart'),
]