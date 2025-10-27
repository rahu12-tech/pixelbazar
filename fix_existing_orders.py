#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
django.setup()

from pixelbazar.models import Order, OrderProduct, Product

# Fix existing orders by adding sample product data
orders = Order.objects.filter(products_data=[])  # Orders with empty products_data

print(f"Found {orders.count()} orders with empty products_data")

# Get a sample product to use as fallback
sample_product = Product.objects.first()
if not sample_product:
    print("No products found in database!")
    sys.exit(1)

for order in orders:
    print(f"Fixing order: {order.order_id}")
    
    # Create sample product data based on order amount
    sample_products_data = [
        {
            '_id': str(sample_product.id),
            'product_name': sample_product.product_name,
            'product_price': float(order.totalAmount or 466),  # Use order total or default
            'product_img': f'/media/products/{sample_product.product_img.name}' if sample_product.product_img else '',
            'quantity': 1,
            'product_return': str(sample_product.product_return)
        }
    ]
    
    # Update the order with sample product data
    order.products_data = sample_products_data
    order.save()
    
    # Also create OrderProduct relationship if it doesn't exist
    if not OrderProduct.objects.filter(order=order).exists():
        OrderProduct.objects.create(
            order=order,
            product=sample_product,
            quantity=1
        )
    
    print(f"  Updated order {order.order_id} with product data")

print("All orders fixed!")