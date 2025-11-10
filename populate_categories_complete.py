import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
django.setup()

from pixelbazar.models import Category, Subcategory

def populate_categories_and_subcategories():
    print("Starting to populate categories and subcategories...")
    
    # Category and Subcategory mapping
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
    
    created_categories = 0
    created_subcategories = 0
    
    # Create categories and subcategories
    for slug, data in categories_data.items():
        # Create or get category
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': data['name'],
                'is_active': True,
                'display_order': created_categories
            }
        )
        
        if created:
            created_categories += 1
            print(f"Created category: {category.name}")
        else:
            print(f"Category already exists: {category.name}")
        
        # Create subcategories for this category
        for sub_slug, sub_name in data['subcategories']:
            subcategory, sub_created = Subcategory.objects.get_or_create(
                slug=sub_slug,
                defaults={
                    'name': sub_name,
                    'category': category,
                    'is_active': True
                }
            )
            
            if sub_created:
                created_subcategories += 1
                print(f"  Created subcategory: {subcategory.name}")
            else:
                print(f"  Subcategory already exists: {subcategory.name}")
    
    print(f"\nPopulation complete!")
    print(f"Categories created: {created_categories}")
    print(f"Subcategories created: {created_subcategories}")
    print(f"Total categories: {Category.objects.count()}")
    print(f"Total subcategories: {Subcategory.objects.count()}")
    
    # Show final structure
    print(f"\nFinal Category Structure:")
    for category in Category.objects.all().order_by('display_order'):
        print(f"{category.name} ({category.slug})")
        for subcategory in category.subcategories_list.all():
            print(f"  - {subcategory.name} ({subcategory.slug})")

if __name__ == '__main__':
    populate_categories_and_subcategories()