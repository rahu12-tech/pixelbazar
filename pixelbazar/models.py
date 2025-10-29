from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from datetime import datetime, timedelta
from django.utils import timezone
import uuid

# Product Stock
class ProductStock(models.Model):
    STATUS_CHOICES = [
        ("stock", "Stock"),
        ("outofstock", "Out of Stock")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="stock")

# Product Model
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('phones', 'Phones'),
        ('laptops', 'Laptops'),
        ('speakers', 'Speakers'),
        ('headphones', 'Headphones'),
        ('cameras', 'Cameras'),
        ('music', 'Music'),
        ('electronics', 'Electronics'),
    ]
    
    product_name = models.CharField(max_length=200)
    product_titel = models.CharField(max_length=300)
    product_price = models.FloatField()
    product_oldPrice = models.FloatField(null=True, blank=True)
    product_discount = models.CharField(max_length=20, null=True, blank=True)
    product_brand = models.CharField(max_length=100)
    product_type = models.CharField(max_length=100)
    product_warranty = models.CharField(max_length=100, null=True, blank=True)
    product_des = models.TextField()
    product_img = models.ImageField(upload_to='products/')
    product_return = models.IntegerField(default=0)
    product_IsStock = models.OneToOneField(ProductStock, on_delete=models.CASCADE, related_name='product', null=True, blank=True)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    product_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_flash_sale = models.BooleanField(default=False)
    last_sale_date = models.DateTimeField(null=True, blank=True)
    sales_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    profilePic = models.ImageField(null=True, blank=True)
    number = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, default="user")  # admin/user
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.__class__(email=email, **extra_fields)
        user.set_password(password)  # ✅ password hash ho jaayega
        user.save(using=self._db)
        return user

# Address Model
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    locality = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    landmark = models.CharField(max_length=200, null=True, blank=True)
    alternate_phone = models.CharField(max_length=15, null=True, blank=True)
    address_type = models.CharField(max_length=20, choices=[('home', 'Home'), ('work', 'Work')], default='home')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

# Contact Model
class Contact(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    number = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"

# Order Tracking
class OrderTracking(models.Model):
    STATUS_CHOICES = [
        ("Order Placed", "Order Placed"),
        ("Confirmed", "Confirmed"),
        ("Packaging", "Packaging"),
        ("Shipped", "Shipped"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Order Placed")
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    tracking_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    delivery_partner = models.CharField(max_length=100, null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = f"TRK{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

# Return/Refund Status
class ReturnStatus(models.Model):
    STATUS_CHOICES = [
        ("requested", "Return Requested"),
        ("approved", "Return Approved"),
        ("rejected", "Return Rejected"),
        ("picked_up", "Picked Up"),
        ("refund_initiated", "Refund Initiated"),
        ("refund_completed", "Refund Completed")
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    reason = models.TextField(null=True, blank=True)
    return_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    refund_amount = models.FloatField(null=True, blank=True)
    pickup_date = models.DateTimeField(null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.return_id:
            self.return_id = f"RET{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

# Default function for OrderTracking
def default_tracking():
    tracking = OrderTracking.objects.create()
    return tracking.id

# Payment Model
class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    PAYMENT_METHOD = [
        ('razorpay', 'Razorpay'),
        ('cod', 'Cash on Delivery'),
        ('wallet', 'Wallet')
    ]
    payment_id = models.CharField(max_length=100, unique=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

# Order Model
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('razorpay', 'Online Payment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    products = models.ManyToManyField(Product, through='OrderProduct')
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True, blank=True)
    
    # Customer Details
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    town = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    # Store complete product data as JSON
    products_data = models.JSONField(default=list, blank=True)
    
    totalAmount = models.FloatField(default=0.0)
    discount_amount = models.FloatField(default=0.0)
    delivery_charges = models.FloatField(default=0.0)
    final_amount = models.FloatField(default=0.0)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, null=True, blank=True)
    tracking = models.OneToOneField(OrderTracking, on_delete=models.CASCADE, default=default_tracking)
    return_status = models.OneToOneField(ReturnStatus, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    # Direct payment fields for easier access
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"ORD{random.randint(100000000, 999999999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_id}"

# OrderProduct to store quantity
class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

# OrderItem for detailed product tracking
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_img = models.URLField()
    quantity = models.IntegerField(default=1)




class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)



class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)



class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        # timezone-aware datetime se compare kar rahe hain
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.otp}"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount = models.IntegerField()  # percentage
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_till = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.discount}%"

class GiftCard(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='gift_cards/')
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

class MusicBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=100)
    image = models.ImageField(upload_to='banners/')
    category = models.CharField(max_length=50, default='music')
    products = models.ManyToManyField(Product, blank=True, related_name='music_banners')
    price_range_min = models.FloatField(null=True, blank=True)
    price_range_max = models.FloatField(null=True, blank=True)
    discount_text = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name