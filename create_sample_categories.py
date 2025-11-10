#!/usr/bin/env python
import os
import django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
    django.setup()
    
    from pixelbazar.models import Category
    
    # Create main categories
    categories_data = [
        {'name': 'Mobiles & Tablets', 'slug': 'mobiles-tablets'},
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Fashion', 'slug': 'fashion'},
        {'name': 'Home & Kitchen', 'slug': 'home-kitchen'},
        {'name': 'Books & Media', 'slug': 'books-media'},
        {'name': 'Sports & Fitness', 'slug': 'sports-fitness'},
    ]
    
    # Create subcategories
    subcategories_data = [
        # Mobiles & Tablets subcategories
        {'name': 'Smartphones', 'slug': 'smartphones', 'parent': 'Mobiles & Tablets'},
        {'name': 'Tablets', 'slug': 'tablets', 'parent': 'Mobiles & Tablets'},
        {'name': 'Mobile Accessories', 'slug': 'mobile-accessories', 'parent': 'Mobiles & Tablets'},
        
        # Electronics subcategories
        {'name': 'Laptops', 'slug': 'laptops', 'parent': 'Electronics'},
        {'name': 'Headphones', 'slug': 'headphones', 'parent': 'Electronics'},
        {'name': 'Speakers', 'slug': 'speakers', 'parent': 'Electronics'},
        {'name': 'Cameras', 'slug': 'cameras', 'parent': 'Electronics'},
        
        # Fashion subcategories
        {'name': 'Men Clothing', 'slug': 'men-clothing', 'parent': 'Fashion'},
        {'name': 'Women Clothing', 'slug': 'women-clothing', 'parent': 'Fashion'},
        {'name': 'Footwear', 'slug': 'footwear', 'parent': 'Fashion'},
    ]
    
    print("Creating main categories...")
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'slug': cat_data['slug']}
        )
        if created:
            print(f"Created: {category.name}")
        else:
            print(f"Already exists: {category.name}")
    
    print("\nCreating subcategories...")
    for subcat_data in subcategories_data:
        try:
            parent_category = Category.objects.get(name=subcat_data['parent'])
            subcategory, created = Category.objects.get_or_create(
                name=subcat_data['name'],
                defaults={
                    'slug': subcat_data['slug'],
                    'parent_category': parent_category
                }
            )
            if created:
                print(f"Created: {subcategory.name} under {parent_category.name}")
            else:
                print(f"Already exists: {subcategory.name}")
        except Category.DoesNotExist:
            print(f"Parent category '{subcat_data['parent']}' not found")
    
    print(f"\nSample categories created successfully!")
    print(f"Total categories: {Category.objects.count()}")