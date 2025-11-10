from django.contrib import admin
from django import forms
from .models import *

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class ProductAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Category change par subcategory filter karo
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories_list.all()
        else:
            self.fields['subcategory'].queryset = Subcategory.objects.none()
    
    class Meta:
        model = Product
        fields = '__all__'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('profilePic', 'number', 'gender', 'role', 'location_lat', 'location_lng')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('email', 'profilePic', 'number', 'gender', 'role')}),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['product_name', 'product_price', 'category', 'subcategory', 'is_flash_sale', 'is_featured', 'is_trending', 'sales_count']
    list_filter = ['product_type', 'category', 'subcategory', 'is_flash_sale', 'is_featured', 'is_trending', 'created_at']
    list_editable = ['is_flash_sale', 'is_featured', 'is_trending']
    search_fields = ['product_name', 'product_brand']
    readonly_fields = ['sales_count', 'last_sale_date', 'created_at']
    autocomplete_fields = ['category', 'subcategory']
    
    class Media:
        js = ('admin/js/dynamic_subcategory.js',)
    
    def save_model(self, request, obj, form, change):
        if obj.category:
            obj.product_category = obj.category.slug
        super().save_model(request, obj, form, change)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'city', 'state', 'is_default']
    list_filter = ['city', 'state', 'address_type']
    search_fields = ['name', 'city', 'state']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'final_amount', 'status', 'payment_status', 'payment_method', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__email']
    readonly_fields = ['order_id', 'created_at']
    
    def payment_status(self, obj):
        return obj.payment.status if obj.payment else 'No Payment'
    payment_status.short_description = 'Payment Status'
    
    def payment_method(self, obj):
        return obj.payment.method.upper() if obj.payment else 'N/A'
    payment_method.short_description = 'Payment Method'

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['tracking_id', 'status', 'delivery_partner', 'updatedAt']
    list_filter = ['status', 'delivery_partner']
    search_fields = ['tracking_id']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'amount', 'status', 'method', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['payment_id', 'razorpay_payment_id']
    readonly_fields = ['payment_id', 'created_at']

@admin.register(ReturnStatus)
class ReturnStatusAdmin(admin.ModelAdmin):
    list_display = ['return_id', 'status', 'refund_amount', 'updatedAt']
    list_filter = ['status', 'updatedAt']
    search_fields = ['return_id']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'product__product_name']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__email', 'product__product_name']

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'number', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'number']
    readonly_fields = ['created_at']
    actions = ['mark_as_read', 'mark_as_unread']
    list_editable = ['is_read']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected contacts as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected contacts as unread"

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'discount', 'min_amount', 'max_discount', 'valid_till', 'is_active']
    list_filter = ['is_active', 'valid_till', 'created_at']
    search_fields = ['code', 'title']
    readonly_fields = ['created_at']

@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'category']
    readonly_fields = ['created_at']

@admin.register(MusicBanner)
class MusicBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'category', 'price_range_min', 'price_range_max', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active']
    filter_horizontal = ['products']
    fieldsets = (
        ('Banner Information', {
            'fields': ('title', 'subtitle', 'image', 'category', 'is_active')
        }),
        ('Products & Pricing', {
            'fields': ('products', 'price_range_min', 'price_range_max', 'discount_text')
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'slug', 'is_active', 'created_at']
    list_filter = ['parent_category', 'is_active', 'created_at']
    search_fields = ['name', 'slug']
    list_editable = ['is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_category')

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'slug']
    list_editable = ['is_active']
    autocomplete_fields = ['category']

admin.site.register(ProductStock)
admin.site.register(OrderProduct)
admin.site.register(OrderItem)
admin.site.register(OTP)