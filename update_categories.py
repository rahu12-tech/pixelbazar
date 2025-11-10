#!/usr/bin/env python
import os
import django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
    django.setup()
    
    from pixelbazar.models import Category, Product
    
    # Delete old categories first
    print("Deleting old categories...")
    Category.objects.all().delete()
    
    # Create new categories with proper slugs
    new_categories = [
        {'name': 'Mobiles & Tablets', 'slug': 'mobiles-tablets', 'display_order': 1},
        {'name': 'Electronics', 'slug': 'electronics', 'display_order': 2},
        {'name': 'Fashion', 'slug': 'fashion', 'display_order': 3},
        {'name': 'Home & Furniture', 'slug': 'home-furniture', 'display_order': 4},
        {'name': 'TV & Appliances', 'slug': 'tv-appliances', 'display_order': 5},
        {'name': 'Beauty', 'slug': 'beauty', 'display_order': 6},
        {'name': 'Food & Grocery', 'slug': 'food-grocery', 'display_order': 7},
    ]
    
    print("Creating new categories...")
    for cat_data in new_categories:
        category = Category.objects.create(
            name=cat_data['name'],
            slug=cat_data['slug'],
            display_order=cat_data['display_order'],
            is_active=True
        )
        print(f"Created: {category.name}")
    
    # Update existing products to use new category values
    print("\nUpdating product categories...")
    
    # Map old categories to new ones
    category_mapping = {
        'phones': 'mobiles-tablets',
        'laptops': 'electronics',
        'speakers': 'electronics',
        'headphones': 'electronics',
        'cameras': 'electronics',
        'music': 'electronics',
        'electronics': 'electronics',
    }
    
    for old_cat, new_cat in category_mapping.items():
        updated_count = Product.objects.filter(product_category=old_cat).update(product_category=new_cat)
        if updated_count > 0:
            print(f"Updated {updated_count} products from '{old_cat}' to '{new_cat}'")
    
    print(f"\nTotal categories: {Category.objects.count()}")
    print(f"Total products: {Product.objects.count()}")
    print("Categories update completed successfully!")