import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
django.setup()

from pixelbazar.models import Category, Subcategory

def populate_categories():
    # Categories and their subcategories
    categories_data = {
        'mobiles-tablets': {
            'name': 'Mobiles & Tablets',
            'subcategories': [
                ('smartphones', 'Smartphones'),
                ('tablets', 'Tablets'),
                ('mobile-accessories', 'Mobile Accessories'),
            ]
        },
        'electronics': {
            'name': 'Electronics',
            'subcategories': [
                ('laptops', 'Laptops'),
                ('headphones', 'Headphones'),
                ('speakers', 'Speakers'),
                ('cameras', 'Cameras'),
                ('gaming', 'Gaming'),
            ]
        },
        'fashion': {
            'name': 'Fashion',
            'subcategories': [
                ('mens-clothing', 'Men\'s Clothing'),
                ('womens-clothing', 'Women\'s Clothing'),
                ('footwear', 'Footwear'),
                ('accessories', 'Accessories'),
            ]
        },
        'home-furniture': {
            'name': 'Home & Furniture',
            'subcategories': [
                ('furniture', 'Furniture'),
                ('home-decor', 'Home Decor'),
                ('kitchen', 'Kitchen'),
            ]
        },
        'tv-appliances': {
            'name': 'TV & Appliances',
            'subcategories': [
                ('televisions', 'Televisions'),
                ('refrigerators', 'Refrigerators'),
                ('washing-machines', 'Washing Machines'),
                ('air-conditioners', 'Air Conditioners'),
            ]
        },
        'beauty': {
            'name': 'Beauty',
            'subcategories': [
                ('skincare', 'Skincare'),
                ('makeup', 'Makeup'),
                ('haircare', 'Haircare'),
            ]
        },
        'food-grocery': {
            'name': 'Food & Grocery',
            'subcategories': [
                ('fruits-vegetables', 'Fruits & Vegetables'),
                ('dairy', 'Dairy'),
                ('snacks', 'Snacks'),
            ]
        }
    }
    
    print("Creating categories and subcategories...")
    
    for slug, data in categories_data.items():
        # Create or get category
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': data['name']}
        )
        
        if created:
            print(f"Created category: {category.name}")
        else:
            print(f"Category exists: {category.name}")
        
        # Create subcategories
        for sub_slug, sub_name in data['subcategories']:
            subcategory, created = Subcategory.objects.get_or_create(
                slug=sub_slug,
                defaults={
                    'name': sub_name,
                    'category': category
                }
            )
            
            if created:
                print(f"  Created subcategory: {sub_name}")
            else:
                print(f"  Subcategory exists: {sub_name}")
    
    print(f"\nTotal Categories: {Category.objects.count()}")
    print(f"Total Subcategories: {Subcategory.objects.count()}")
    print("All categories and subcategories populated!")

if __name__ == '__main__':
    populate_categories()