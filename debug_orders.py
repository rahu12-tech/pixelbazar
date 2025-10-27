#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
django.setup()

from pixelbazar.models import Order, OrderProduct

# Debug existing orders
orders = Order.objects.all()
print(f"Total orders: {orders.count()}")

for order in orders:
    print(f"\nOrder ID: {order.order_id}")
    print(f"User: {order.user.email if order.user else 'No user'}")
    print(f"Address fields:")
    print(f"  fname: '{order.fname}'")
    print(f"  lname: '{order.lname}'")
    print(f"  address: '{order.address}'")
    print(f"  city: '{order.city}'")
    print(f"  mobile: '{order.mobile}'")
    print(f"Products data: {order.products_data}")
    
    # Check OrderProduct relationship
    order_products = OrderProduct.objects.filter(order=order)
    print(f"OrderProduct count: {order_products.count()}")
    for op in order_products:
        print(f"  - {op.product.product_name} (qty: {op.quantity})")