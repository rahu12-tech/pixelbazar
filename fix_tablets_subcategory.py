import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
django.setup()

from pixelbazar.models import Category, Subcategory

def fix_tablets_subcategory():
    print("Fixing Tablets subcategory...")
    
    try:
        # Get Mobiles & Tablets category
        mobiles_category = Category.objects.get(slug='mobiles-tablets')
        
        # Fix the existing "phone" subcategory to "Tablets"
        try:
            phone_subcategory = Subcategory.objects.get(slug='tablets', category=mobiles_category)
            phone_subcategory.name = 'Tablets'
            phone_subcategory.save()
            print(f"Updated subcategory to: {phone_subcategory.name}")
        except Subcategory.DoesNotExist:
            # Create Tablets subcategory if it doesn't exist
            tablets_subcategory = Subcategory.objects.create(
                name='Tablets',
                slug='tablets',
                category=mobiles_category,
                is_active=True
            )
            print(f"Created new subcategory: {tablets_subcategory.name}")
        
        # Show updated structure for Mobiles & Tablets
        print(f"\nUpdated {mobiles_category.name} subcategories:")
        for subcategory in mobiles_category.subcategories_list.all().order_by('name'):
            print(f"  - {subcategory.name} ({subcategory.slug})")
            
    except Category.DoesNotExist:
        print("Mobiles & Tablets category not found!")

if __name__ == '__main__':
    fix_tablets_subcategory()