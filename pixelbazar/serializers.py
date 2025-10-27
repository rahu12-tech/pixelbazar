from rest_framework import serializers
from .models import *

class ProductStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStock
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    product_IsStock = ProductStockSerializer(read_only=True)
    product_img = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_product_img(self, obj):
        if obj.product_img:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product_img.url)
            return obj.product_img.url
        return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profilePic', 'number', 'gender']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'total_price', 'created_at']
    
    def get_total_price(self, obj):
        return obj.product.product_price * obj.quantity

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']

class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = '__all__'

class ReturnStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnStatus
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity', 'total_price']
    
    def get_total_price(self, obj):
        return obj.product.product_price * obj.quantity

class OrderSerializer(serializers.ModelSerializer):
    tracking = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    paymentMethod = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'fname', 'lname', 'email', 'mobile', 'address', 'town',
            'city', 'state', 'pincode', 'products', 'total_amount', 'final_amount',
            'paymentMethod', 'payment', 'tracking', 'createdAt'
        ]
    
    def get_total_amount(self, obj):
        return obj.totalAmount or 0
    
    def get_paymentMethod(self, obj):
        return obj.payment_method or 'COD'
    
    def get_products(self, obj):
        # Return products_data if available, otherwise get from OrderProduct
        if obj.products_data:
            return obj.products_data
        
        # Fallback to OrderProduct relationship
        order_products = obj.orderproduct_set.all()
        products_list = []
        for op in order_products:
            product_data = {
                '_id': str(op.product.id),
                'product_name': op.product.product_name,
                'product_price': op.product.product_price,
                'product_img': self.context['request'].build_absolute_uri(op.product.product_img.url) if op.product.product_img else '',
                'quantity': op.quantity,
                'product_return': str(op.product.product_return)
            }
            products_list.append(product_data)
        return products_list
    
    def get_tracking(self, obj):
        if obj.tracking:
            return {
                'status': obj.tracking.status,
                'updatedAt': obj.tracking.updatedAt.isoformat() if obj.tracking.updatedAt else obj.created_at.isoformat()
            }
        return {'status': 'Order Placed', 'updatedAt': obj.created_at.isoformat()}
    
    def get_payment(self, obj):
        return {
            'method': obj.payment_method or 'COD',
            'status': obj.payment_status or 'pending'
        }

class OrderDetailSerializer(OrderSerializer):
    return_status = ReturnStatusSerializer(read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ['return_status']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'number', 'message', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at']

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['email', 'otp', 'is_verified']

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'description', 'is_active']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None