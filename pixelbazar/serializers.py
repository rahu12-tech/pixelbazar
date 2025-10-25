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
    tracking = OrderTrackingSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    return_status = ReturnStatusSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'totalAmount', 'delivery_charges', 'final_amount',
            'status', 'created_at', 'tracking', 'payment', 'return_status',
            'shipping_address', 'products_count'
        ]
    
    def get_products_count(self, obj):
        return obj.orderproduct_set.count()

class OrderDetailSerializer(serializers.ModelSerializer):
    tracking = OrderTrackingSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    return_status = ReturnStatusSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    order_products = OrderProductSerializer(source='orderproduct_set', many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'totalAmount', 'discount_amount', 'delivery_charges', 
            'final_amount', 'status', 'created_at', 'updated_at', 'tracking', 
            'payment', 'return_status', 'shipping_address', 'order_products'
        ]

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