# Debug API to list all products
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product

@api_view(['GET'])
def debug_products(request):
    try:
        products = Product.objects.all()
        products_data = []
        
        for product in products:
            image_url = None
            if product.product_img:
                try:
                    image_url = request.build_absolute_uri(product.product_img.url)
                except:
                    image_url = str(product.product_img)
            
            products_data.append({
                'id': product.id,
                'name': product.product_name,
                'title': product.product_titel,
                'brand': product.product_brand,
                'price': product.product_price,
                'image': image_url,
                'type': product.product_type
            })
        
        return Response({
            'status': 200,
            'products': products_data,
            'total_products': len(products_data)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)