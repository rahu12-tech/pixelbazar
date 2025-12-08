from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import *
from .serializers import *
import razorpay
from django.conf import settings
import hashlib
import hmac
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
import random
from django.core.mail import send_mail
from .email_utils import send_email_via_brevo
from django.http import JsonResponse

# Razorpay client - initialize only when needed
def get_razorpay_client():
    print(f"Initializing Razorpay with Key: {settings.RAZORPAY_KEY_ID}")
    print(f"Secret length: {len(settings.RAZORPAY_KEY_SECRET)}")
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    return client

# User Profile API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        user = request.user
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'number': user.number,
            'gender': user.gender,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'profilePic': request.build_absolute_uri(user.profilePic.url) if user.profilePic else None
        }
        return Response({'user': user_data})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# Update User Profile API  
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    try:
        user = request.user
        
        # Update fields
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        if 'number' in request.data:
            user.number = request.data['number']
        if 'gender' in request.data:
            user.gender = request.data['gender']
            
        user.save()
        
        return Response({
            'msg': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'number': user.number,
                'gender': user.gender,
                'email': user.email
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# Token Refresh API
@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        return Response({
            'access': access_token,
            'refresh': str(refresh)
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

# Signup API
@api_view(['POST'])
def signup(request):
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')
    location = request.data.get('location', {})

    if not all([name, email, password]):
        return Response({'msg': 'All fields required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'msg': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    otp_code = str(random.randint(100000, 999999))
    OTP.objects.filter(email=email).delete()  # Remove old OTPs
    OTP.objects.create(email=email, otp=otp_code)

    # Always send email in production, but also return OTP in debug mode
    import sys
    print("SIGNUP VIEW CALLED - Sending OTP...")
    sys.stdout.flush()
    
    try:
        success, response = send_email_via_brevo(
            email,
            'Your OTP Code',
            f'Your OTP code is: {otp_code}'
        )
        if success:
            if settings.DEBUG:
                return Response({'msg': 'OTP sent', 'otp': otp_code})
            else:
                return Response({'msg': 'OTP sent'})
        else:
            print("Brevo email error:", response)
            # In debug mode, return OTP even if email fails
            if settings.DEBUG:
                return Response({'msg': 'OTP generated (email failed)', 'otp': otp_code})
            return Response({'msg': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print("Email send error:", e)
        # In debug mode, return OTP even if email fails
        if settings.DEBUG:
            return Response({'msg': 'OTP generated (email error)', 'otp': otp_code})
        return Response({'msg': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    otp_code = request.data.get('otp')
    password = request.data.get('password')
    name = request.data.get('name', '')
    location = request.data.get('location', {})

    try:
        otp_obj = OTP.objects.get(email=email, otp=otp_code)

        if otp_obj.is_expired():  # Make sure OTP model has is_expired method
            return Response({'msg': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Create user (prevent duplicates)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': name,
                'password': make_password(password),
                'location_lat': location.get('lat'),
                'location_lng': location.get('lng')
            }
        )

        otp_obj.is_verified = True
        otp_obj.save()

        return Response({'msg': 'User created successfully'})
    except OTP.DoesNotExist:
        return Response({'msg': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

# Login API
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not all([email, password]):
        return Response({'msg': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        if check_password(password, user.password):
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            return Response({
                'status': 200,
                'usertoken': access_token,
                'refresh': str(refresh),
                'exitsuser': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'role': 'admin' if (user.is_staff or user.is_superuser) else 'user'
                }
            })
        else:
            return Response({'msg': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'msg': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# Product APIs
@api_view(['GET'])
def get_products(request):
    products = Product.objects.select_related('category', 'subcategory').all()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_product_detail(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Enhanced product details with return policy
        product_data = {
            'id': product.id,
            'product_name': product.product_name,
            'product_titel': product.product_titel,
            'product_price': product.product_price,
            'product_oldPrice': product.product_oldPrice,
            'product_discount': product.product_discount,
            'product_brand': product.product_brand,
            'product_type': product.product_type,
            'product_warranty': product.product_warranty,
            'product_des': product.product_des,
            'product_img': request.build_absolute_uri(product.product_img.url) if product.product_img else None,
            'product_category': product.product_category,
            'is_featured': product.is_featured,
            'is_trending': product.is_trending,
            'is_flash_sale': product.is_flash_sale,
            'sales_count': product.sales_count,
            # Enhanced Return Policy Details
            'return_policy': {
                'is_returnable': getattr(product, 'is_returnable', True),
                'return_days': getattr(product, 'return_policy_days', 7),
                'return_policy_text': getattr(product, 'return_policy_text', None) or (f"Free delivery & return in {getattr(product, 'return_policy_days', 7)} days" if getattr(product, 'return_policy_days', 7) > 0 else "No return policy"),
                'return_conditions': [
                    'Product should be unused and in original packaging',
                    'All accessories and tags should be intact',
                    f'Return request should be raised within {getattr(product, "return_policy_days", 7)} days of delivery'
                ] if getattr(product, 'is_returnable', True) else []
            },
            'stock_status': product.product_IsStock.status if product.product_IsStock else 'stock'
        }
        
        return Response(product_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_products(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.select_related('category', 'subcategory').filter(
            Q(product_name__icontains=query) | 
            Q(product_brand__icontains=query) |
            Q(product_type__icontains=query)
        )
    else:
        products = Product.objects.select_related('category', 'subcategory').all()
    
    data = []
    for product in products:
        product_data = {
            'id': product.id,
            'product_name': product.product_name,
            'product_titel': product.product_titel,
            'product_price': product.product_price,
            'product_oldPrice': product.product_oldPrice,
            'product_discount': product.product_discount,
            'product_brand': product.product_brand,
            'product_img': request.build_absolute_uri(product.product_img.url) if product.product_img else None,
            'product_category': product.category.slug if product.category else product.product_category,
            'category': {
                'name': product.category.name,
                'slug': product.category.slug
            } if product.category else None,
            'subcategory': {
                'name': product.subcategory.name,
                'slug': product.subcategory.slug
            } if product.subcategory else None
        }
        data.append(product_data)
    return Response(data)

# Cart APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    serializer = CartSerializer(cart_items, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user, 
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += int(quantity)
        cart_item.save()
    
    return Response({'message': 'Product added to cart'}, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    quantity = request.data.get('quantity', 1)
    cart_item.quantity = quantity
    cart_item.save()
    return Response({'message': 'Cart updated'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    return Response({'message': 'Item removed from cart'})

# Wishlist APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        wishlist_data = []
        
        for item in wishlist_items:
            wishlist_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product': {
                    'id': item.product.id,
                    'product_name': item.product.product_name,
                    'product_price': item.product.product_price,
                    'product_oldPrice': item.product.product_oldPrice,
                    'product_img': request.build_absolute_uri(item.product.product_img.url) if item.product.product_img else None,
                    'product_brand': item.product.product_brand,
                    'product_type': item.product.product_type
                },
                'added_at': item.added_at
            })
        
        return Response({'data': wishlist_data})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    try:
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({
                'status': 200,
                'message': 'Product added to wishlist successfully'
            })
        else:
            return Response({
                'status': 200,
                'message': 'Product already in wishlist'
            })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, wishlist_id):
    try:
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
        wishlist_item.delete()
        
        return Response({
            'status': 200,
            'message': 'Product removed from wishlist'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# Address APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    serializer = AddressSerializer(addresses, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_address(request):
    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    serializer = AddressSerializer(address, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    return Response({'message': 'Address deleted'})

# Checkout & Payment APIs
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    address_id = request.data.get('address_id')
    payment_method = request.data.get('payment_method', 'razorpay')
    
    # Get cart items
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate total
    total_amount = sum(item.product.product_price * item.quantity for item in cart_items)
    delivery_charges = 40 if total_amount < 500 else 0
    final_amount = total_amount + delivery_charges
    
    # Get address
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        totalAmount=total_amount,
        delivery_charges=delivery_charges,
        final_amount=final_amount
    )
    
    # Set estimated delivery date
    from datetime import datetime, timedelta
    order.tracking.estimated_delivery = order.created_at + timedelta(days=5)
    order.tracking.delivery_partner = 'Bazar Express'
    order.tracking.save()
    
    # Add products to order
    for cart_item in cart_items:
        OrderProduct.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity
        )
    
    # Create payment
    if payment_method == 'razorpay':
        # Create Razorpay order
        razorpay_client = get_razorpay_client()
        razorpay_order = razorpay_client.order.create({
            'amount': int(final_amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1
        })
        
        payment = Payment.objects.create(
            razorpay_order_id=razorpay_order['id'],
            amount=final_amount,
            method='razorpay'
        )
        order.payment = payment
        order.save()
        
        # Clear cart
        cart_items.delete()
        
        return Response({
            'order_id': order.order_id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': final_amount,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
            'expected_delivery': order.tracking.estimated_delivery
        })
    
    elif payment_method == 'cod':
        payment = Payment.objects.create(
            amount=final_amount,
            method='cod',
            status='pending'
        )
        order.payment = payment
        order.status = 'confirmed'
        order.tracking.status = 'Confirmed'
        order.tracking.save()
        order.save()
        
        # Update product sales count for COD orders
        from django.utils import timezone
        order_products = OrderProduct.objects.filter(order=order)
        for order_product in order_products:
            product = order_product.product
            product.sales_count += order_product.quantity
            product.last_sale_date = timezone.now()
            product.save()
        
        # Clear cart
        cart_items.delete()
        
        return Response({
            'order_id': order.order_id,
            'message': 'Order placed successfully',
            'expected_delivery': order.tracking.estimated_delivery
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    # Verify signature
    body = razorpay_order_id + "|" + razorpay_payment_id
    expected_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=body.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if expected_signature == razorpay_signature:
        # Payment successful
        payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'completed'
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'confirmed'
        order.tracking.status = 'Confirmed'
        
        # Set estimated delivery if not already set
        if not order.tracking.estimated_delivery:
            from datetime import datetime, timedelta
            order.tracking.estimated_delivery = order.created_at + timedelta(days=5)
        
        order.tracking.save()
        order.save()
        
        return Response({
            'message': 'Payment verified successfully',
            'order_id': order.order_id,
            'status': 'confirmed'
        })
    else:
        return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

# Order History APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_history(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        order_data = []
        
        for order in orders:
            # Get products data - prioritize products_data JSON field
            products_list = []
            if order.products_data and len(order.products_data) > 0:
                products_list = order.products_data
            else:
                # Fallback to OrderProduct relationship
                order_products = OrderProduct.objects.filter(order=order)
                for op in order_products:
                    image_url = None
                    if op.product.product_img:
                        try:
                            image_url = request.build_absolute_uri(op.product.product_img.url)
                        except:
                            image_url = None
                    
                    products_list.append({
                        '_id': str(op.product.id),
                        'product_name': op.product.product_name,
                        'product_price': op.product.product_price,
                        'product_img': image_url,
                        'quantity': op.quantity
                    })
            
            order_info = {
                'order_id': order.order_id,
                'total_amount': order.totalAmount or 0,
                'final_amount': order.final_amount or 0,
                'fname': order.fname or '',
                'lname': order.lname or '',
                'email': order.email or '',
                'mobile': order.mobile or '',
                'address': order.address or '',
                'town': order.town or '',
                'city': order.city or '',
                'state': order.state or '',
                'pincode': order.pincode or '',
                'paymentMethod': order.payment_method or 'COD',
                'payment': {
                    'method': order.payment_method or 'COD',
                    'status': order.payment_status or 'pending'
                },
                'tracking': {
                    'status': order.tracking.status if order.tracking else 'Order Placed',
                    'updatedAt': order.tracking.updatedAt.isoformat() if order.tracking and order.tracking.updatedAt else order.created_at.isoformat()
                },
                'createdAt': order.created_at.isoformat(),
                'products': products_list,
                'return_requests': [
                    {
                        'return_id': order.return_status.return_id,
                        'status': order.return_status.status,
                        'reason': order.return_status.reason,
                        'refund_amount': order.return_status.refund_amount,
                        'created_at': order.return_status.updatedAt.isoformat()
                    }
                ] if order.return_status else []
            }
            order_data.append(order_info)
        
        return Response({
            'status': 200,
            'orders': order_data,
            'total_orders': len(order_data)
        })
    except Exception as e:
        print(f"Order history error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Get order products
        order_products = OrderProduct.objects.filter(order=order)
        products_list = []
        
        for op in order_products:
            # Ensure proper image URL
            image_url = None
            if op.product.product_img:
                try:
                    image_url = request.build_absolute_uri(op.product.product_img.url)
                except:
                    image_url = None
            
            products_list.append({
                'id': op.product.id,
                'name': op.product.product_name,
                'title': op.product.product_titel,
                'brand': op.product.product_brand,
                'price': op.product.product_price,
                'image': image_url,
                'quantity': op.quantity,
                'total': op.product.product_price * op.quantity
            })
        
        # Calculate expected delivery date if not set
        expected_delivery = order.tracking.estimated_delivery
        if not expected_delivery and order.tracking.status not in ['Delivered', 'Cancelled']:
            from datetime import datetime, timedelta
            expected_delivery = order.created_at + timedelta(days=5)
        
        # Dynamic payment status based on method
        payment_status = 'pending'
        payment_method = 'COD'
        if order.payment:
            payment_method = order.payment.method.upper()
            if order.payment.method == 'cod':
                payment_status = 'pending' if order.tracking.status != 'Delivered' else 'paid'
            elif order.payment.method == 'razorpay':
                payment_status = 'paid' if order.payment.status == 'completed' else 'pending'
        
        order_detail = {
            'order_id': order.order_id,
            'total_amount': order.totalAmount,
            'delivery_charges': order.delivery_charges,
            'final_amount': order.final_amount,
            'status': order.status,
            'tracking_status': order.tracking.status,
            'created_at': order.created_at,
            'expected_delivery': expected_delivery,
            'products': products_list,
            'tracking': {
                'status': order.tracking.status,
                'tracking_id': order.tracking.tracking_id,
                'estimated_delivery': expected_delivery,
                'delivery_partner': order.tracking.delivery_partner or 'Bazar Express',
                'last_updated': order.tracking.updatedAt
            },
            'shipping_address': {
                'name': order.shipping_address.name if order.shipping_address else 'N/A',
                'phone': order.shipping_address.phone if order.shipping_address else 'N/A',
                'address': order.shipping_address.address if order.shipping_address else 'N/A',
                'locality': order.shipping_address.locality if order.shipping_address else 'N/A',
                'city': order.shipping_address.city if order.shipping_address else 'N/A',
                'state': order.shipping_address.state if order.shipping_address else 'N/A',
                'pincode': order.shipping_address.pincode if order.shipping_address else 'N/A',
                'landmark': order.shipping_address.landmark if order.shipping_address else '',
                'full_address': f"{order.shipping_address.address}, {order.shipping_address.locality}, {order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}" if order.shipping_address else 'N/A'
            } if order.shipping_address else None,
            'payment': {
                'method': payment_method,
                'status': payment_status,
                'amount': order.payment.amount if order.payment else order.final_amount,
                'payment_id': order.payment.payment_id if order.payment else None
            }
        }
        
        return Response(order_detail)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Order Tracking API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def track_order(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Create tracking timeline
        tracking_timeline = [
            {
                'status': 'Order Placed',
                'description': 'Your order has been placed successfully',
                'timestamp': order.created_at,
                'completed': True
            },
            {
                'status': 'Confirmed',
                'description': 'Order confirmed and being prepared',
                'timestamp': order.created_at,
                'completed': order.tracking.status in ['Confirmed', 'Packaging', 'Shipped', 'Out for Delivery', 'Delivered']
            },
            {
                'status': 'Packaging',
                'description': 'Your order is being packed',
                'timestamp': None,
                'completed': order.tracking.status in ['Packaging', 'Shipped', 'Out for Delivery', 'Delivered']
            },
            {
                'status': 'Shipped',
                'description': 'Your order has been shipped',
                'timestamp': None,
                'completed': order.tracking.status in ['Shipped', 'Out for Delivery', 'Delivered']
            },
            {
                'status': 'Out for Delivery',
                'description': 'Your order is out for delivery',
                'timestamp': None,
                'completed': order.tracking.status in ['Out for Delivery', 'Delivered']
            },
            {
                'status': 'Delivered',
                'description': 'Your order has been delivered',
                'timestamp': None,
                'completed': order.tracking.status == 'Delivered'
            }
        ]
        
        tracking_data = {
            'order_id': order.order_id,
            'current_status': order.tracking.status,
            'tracking_id': order.tracking.tracking_id,
            'estimated_delivery': order.tracking.estimated_delivery,
            'delivery_partner': order.tracking.delivery_partner or 'Bazar Express',
            'last_updated': order.tracking.updatedAt,
            'timeline': tracking_timeline,
            'order_details': {
                'total_amount': order.final_amount,
                'created_at': order.created_at
            }
        }
        
        return Response(tracking_data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Enhanced Return Management APIs
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_return(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        if order.tracking.status != 'Delivered':
            return Response({
                'success': False,
                'message': 'Can only return delivered orders'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if order.return_status:
            return Response({
                'success': False,
                'message': 'Return already requested'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check return eligibility (7 days)
        from datetime import timedelta
        from django.utils import timezone
        delivery_date = order.tracking.updatedAt if order.tracking.status == 'Delivered' else order.created_at
        return_deadline = delivery_date + timedelta(days=7)
        
        if timezone.now() > return_deadline:
            return Response({
                'success': False,
                'message': 'Return period expired (7 days from delivery)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return_status = ReturnStatus.objects.create(
            reason=request.data.get('reason', ''),
            refund_amount=order.final_amount
        )
        
        order.return_status = return_status
        order.save()
        
        return Response({
            'success': True,
            'message': 'Return request submitted',
            'return_id': return_status.return_id,
            'refund_amount': return_status.refund_amount
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_return_status(request, return_id):
    try:
        return_status = get_object_or_404(ReturnStatus, return_id=return_id)
        order = get_object_or_404(Order, return_status=return_status, user=request.user)
        
        # Enhanced timeline with all stages
        timeline = [
            {
                'status': 'Return Requested',
                'description': 'Return request submitted successfully',
                'completed': True,
                'timestamp': return_status.updatedAt
            },
            {
                'status': 'Return Approved',
                'description': 'Return request approved by admin',
                'completed': return_status.status in ['approved', 'pickup_scheduled', 'picked_up', 'received', 'quality_check', 'refund_initiated', 'refund_completed'],
                'timestamp': None
            },
            {
                'status': 'Pickup Scheduled',
                'description': 'Pickup scheduled with delivery partner',
                'completed': return_status.status in ['pickup_scheduled', 'picked_up', 'received', 'quality_check', 'refund_initiated', 'refund_completed'],
                'timestamp': return_status.pickup_date
            },
            {
                'status': 'Picked Up',
                'description': 'Product picked up from your location',
                'completed': return_status.status in ['picked_up', 'received', 'quality_check', 'refund_initiated', 'refund_completed'],
                'timestamp': None
            },
            {
                'status': 'Return Received',
                'description': 'Product received at our warehouse',
                'completed': return_status.status in ['received', 'quality_check', 'refund_initiated', 'refund_completed'],
                'timestamp': None
            },
            {
                'status': 'Quality Check',
                'description': 'Product quality verification in progress',
                'completed': return_status.status in ['quality_check', 'refund_initiated', 'refund_completed'],
                'timestamp': None
            },
            {
                'status': 'Refund Initiated',
                'description': 'Refund process started',
                'completed': return_status.status in ['refund_initiated', 'refund_completed'],
                'timestamp': None
            },
            {
                'status': 'Refund Completed',
                'description': 'Refund credited to your account',
                'completed': return_status.status == 'refund_completed',
                'timestamp': None
            }
        ]
        
        return Response({
            'return_id': return_status.return_id,
            'order_id': order.order_id,
            'status': return_status.status,
            'reason': return_status.reason,
            'refund_amount': return_status.refund_amount,
            'pickup_date': return_status.pickup_date,
            'timeline': timeline,
            'last_updated': return_status.updatedAt
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_returns(request):
    try:
        orders_with_returns = Order.objects.filter(user=request.user, return_status__isnull=False)
        return_data = []
        
        for order in orders_with_returns:
            return_data.append({
                'return_id': order.return_status.return_id,
                'order_id': order.order_id,
                'status': order.return_status.status,
                'reason': order.return_status.reason,
                'refund_amount': order.return_status.refund_amount,
                'created_at': order.return_status.updatedAt
            })
        
        return Response({
            'success': True,
            'returns': return_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_delivery_status(request):
    try:
        user = request.user
        from django.utils import timezone
        
        if user.account_created_at:
            days_since_signup = (timezone.now() - user.account_created_at).days
        else:
            days_since_signup = 999
        
        return Response({
            'free_delivery_eligible': days_since_signup <= 2,
            'days_left': max(0, 2 - days_since_signup),
            'account_age_days': days_since_signup,
            'message': f'Free delivery for {max(0, 2 - days_since_signup)} more days' if days_since_signup <= 2 else 'Free delivery on orders above ₹500'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_admin(request):
    user = request.user
    return Response({
        'is_admin': user.is_staff or user.is_superuser,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'user_id': user.id,
        'email': user.email
    })

# Enhanced Delivery Charge Calculator
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_delivery_charges(request):
    try:
        pincode = request.data.get('pincode')
        cart_total = float(request.data.get('cart_total', 0))
        user = request.user
        
        # Check user's free delivery eligibility (new users get 2 days free delivery)
        if user.account_created_at:
            from django.utils import timezone
            days_since_signup = (timezone.now() - user.account_created_at).days
            if days_since_signup <= 2:
                return Response({
                    'delivery_charges': 0,
                    'free_delivery': True,
                    'message': f'Free delivery for new users! {2 - days_since_signup} days left',
                    'reason': 'new_user_benefit'
                })
        
        # Free delivery for orders above ₹500
        if cart_total >= 500:
            return Response({
                'delivery_charges': 0,
                'free_delivery': True,
                'message': 'Free delivery on orders above ₹500',
                'reason': 'minimum_order_value'
            })
        
        # Distance-based pricing
        metro_cities = ['110001', '400001', '560001', '600001', '700001', '500001']
        
        if pincode[:3] in [city[:3] for city in metro_cities]:
            delivery_charges = 40  # Metro cities
            estimated_days = 3
        else:
            delivery_charges = 60  # Other cities
            estimated_days = 5
        
        return Response({
            'delivery_charges': delivery_charges,
            'free_delivery': False,
            'estimated_days': estimated_days,
            'message': f'Delivery charges: ₹{delivery_charges}',
            'reason': 'standard_charges'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Cancel Order API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Check if order can be cancelled
        if order.tracking.status in ['Delivered', 'Cancelled']:
            return Response({
                'success': False,
                'message': 'Cannot cancel delivered or already cancelled orders'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if order.tracking.status == 'Out for Delivery':
            return Response({
                'success': False,
                'message': 'Cannot cancel order that is out for delivery'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel the order
        order.status = 'cancelled'
        order.tracking.status = 'Cancelled'
        order.tracking.save()
        order.save()
        
        # Handle refund based on payment method
        refund_message = ''
        if order.payment:
            if order.payment.method == 'razorpay' and order.payment.status == 'completed':
                order.payment.status = 'refunded'
                order.payment.save()
                refund_message = ' Refund will be processed within 5-7 business days.'
            elif order.payment.method == 'cod':
                refund_message = ' No payment was made for this order.'
        
        return Response({
            'success': True,
            'message': f'Order cancelled successfully.{refund_message}',
            'order_id': order.order_id,
            'refund_amount': order.final_amount if order.payment and order.payment.method == 'razorpay' else 0
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin API to update order status
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.data.get('status')
        
        if new_status in ['Order Placed', 'Confirmed', 'Packaging', 'Shipped', 'Out for Delivery', 'Delivered', 'Cancelled']:
            order.tracking.status = new_status
            
            # Set estimated delivery for shipped orders
            if new_status == 'Shipped' and not order.tracking.estimated_delivery:
                from datetime import datetime, timedelta
                order.tracking.estimated_delivery = datetime.now() + timedelta(days=3)
            
            # Set delivery partner
            if not order.tracking.delivery_partner:
                order.tracking.delivery_partner = 'Bazar Express'
            
            order.tracking.save()
            
            return Response({
                'message': f'Order status updated to {new_status}',
                'tracking_id': order.tracking.tracking_id
            })
        else:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Download Invoice API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, order_id):
    try:
        from django.http import HttpResponse
        import json
        
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Get order products
        order_products = OrderProduct.objects.filter(order=order)
        products_list = []
        subtotal_before_tax = 0
        
        for op in order_products:
            item_total = op.product.product_price * op.quantity
            subtotal_before_tax += item_total
            
            products_list.append({
                'name': op.product.product_name,
                'title': op.product.product_titel,
                'brand': op.product.product_brand,
                'price': op.product.product_price,
                'quantity': op.quantity,
                'total': item_total,
                'hsn_code': '85171200',  # Generic HSN for mobile phones
                'gst_rate': 18
            })
        
        # Calculate GST (18% for electronics)
        gst_rate = 18
        cgst_rate = gst_rate / 2  # 9%
        sgst_rate = gst_rate / 2  # 9%
        
        cgst_amount = (subtotal_before_tax * cgst_rate) / 100
        sgst_amount = (subtotal_before_tax * sgst_rate) / 100
        total_gst = cgst_amount + sgst_amount
        
        subtotal_with_gst = subtotal_before_tax + total_gst
        final_total = subtotal_with_gst + order.delivery_charges
        
        # Create invoice data
        invoice_data = {
            'invoice_number': f'INV-{order.order_id}',
            'order_id': order.order_id,
            'order_date': order.created_at.strftime('%d/%m/%Y %H:%M'),
            'invoice_date': order.created_at.strftime('%d/%m/%Y'),
            'customer_details': {
                'name': order.user.first_name or order.user.username,
                'email': order.user.email,
                'phone': order.user.number or 'N/A'
            },
            'billing_address': {
                'name': order.shipping_address.name if order.shipping_address else 'N/A',
                'phone': order.shipping_address.phone if order.shipping_address else 'N/A',
                'address': order.shipping_address.address if order.shipping_address else 'N/A',
                'locality': order.shipping_address.locality if order.shipping_address else 'N/A',
                'city': order.shipping_address.city if order.shipping_address else 'N/A',
                'state': order.shipping_address.state if order.shipping_address else 'N/A',
                'pincode': order.shipping_address.pincode if order.shipping_address else 'N/A'
            } if order.shipping_address else None,
            'products': products_list,
            'price_breakdown': {
                'subtotal_before_tax': subtotal_before_tax,
                'cgst_rate': f'{cgst_rate}%',
                'cgst_amount': round(cgst_amount, 2),
                'sgst_rate': f'{sgst_rate}%',
                'sgst_amount': round(sgst_amount, 2),
                'total_gst': round(total_gst, 2),
                'subtotal_with_gst': round(subtotal_with_gst, 2),
                'delivery_charges': order.delivery_charges,
                'final_total': round(final_total, 2)
            },
            'payment_details': {
                'method': order.payment.method.upper() if order.payment else 'COD',
                'status': 'Paid' if (order.payment and order.payment.status == 'completed') else 'Pending',
                'amount': order.final_amount,
                'transaction_id': order.payment.razorpay_payment_id if (order.payment and order.payment.razorpay_payment_id) else 'N/A'
            },
            'company_details': {
                'name': 'Bazar Marketplace Pvt Ltd',
                'address': 'Tech Park, Sector 62, Noida, UP - 201301',
                'gstin': '09ABCDE1234F1Z5',
                'pan': 'ABCDE1234F',
                'email': 'support@bazar.com',
                'phone': '+91-9876543210'
            }
        }
        
        # Return JSON response
        response = HttpResponse(
            json.dumps(invoice_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.json"'
        
        return response
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Legacy Add to Cart API (for backward compatibility)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def legacy_add_to_cart(request):
    product_name = request.data.get('product_name')
    product_price = request.data.get('product_price')
    quantity = request.data.get('quantity', 1)
    
    if not product_name:
        return Response({'error': 'Product name required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find product by name
        product = Product.objects.filter(product_name__icontains=product_name).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Add to cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()
        
        return Response({
            'status': 200,
            'msg': 'Product added to cart successfully',
            'cart_item_id': cart_item.id
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# New Cart APIs for frontend compatibility
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add_api(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    if not product_id:
        return Response({'error': 'Product ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()
        
        return Response({
            'status': 200,
            'msg': 'Product added to cart successfully'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_get_api(request):
    try:
        cart_items = Cart.objects.filter(user=request.user)
        cart_data = []
        
        for item in cart_items:
            cart_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.product_name,
                'product_price': item.product.product_price,
                'product_img': request.build_absolute_uri(item.product.product_img.url) if item.product.product_img else None,
                'quantity': item.quantity
            })
        
        return Response({
            'status': 200,
            'data': cart_data
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cart_update_api(request):
    cart_item_id = request.data.get('cart_item_id')
    quantity = request.data.get('quantity', 1)
    
    try:
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'status': 200,
            'msg': 'Cart updated successfully'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_remove_api(request):
    cart_item_id = request.data.get('cart_item_id')
    
    try:
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
        cart_item.delete()
        
        return Response({
            'status': 200,
            'msg': 'Item removed from cart'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Clear Cart API
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    try:
        # Clear user's cart from database
        Cart.objects.filter(user=request.user).delete()
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

# Get Orders API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        orders_data = []
        for order in orders:
            # Get products data - prioritize products_data JSON field
            products_list = []
            print(f"🔍 RAW Products Data for order {order.order_id}: {order.products_data}")
            print(f"🔍 RAW Products Data type: {type(order.products_data)}")
            print(f"🔍 RAW Products Data length: {len(order.products_data) if order.products_data else 0}")
            
            if order.products_data and len(order.products_data) > 0:
                products_list = order.products_data
                print(f"🔍 Using products_data: {len(products_list)} products")
            else:
                print(f"🔍 Fallback to OrderProduct relationship")
                # Fallback to OrderProduct relationship
                order_products = OrderProduct.objects.filter(order=order)
                print(f"🔍 Found {order_products.count()} OrderProduct records")
                for op in order_products:
                    image_url = None
                    if op.product.product_img:
                        try:
                            image_url = request.build_absolute_uri(op.product.product_img.url)
                        except:
                            image_url = None
                    
                    product_data = {
                        '_id': str(op.product.id),
                        'product_name': op.product.product_name,
                        'product_price': op.product.product_price,
                        'product_img': image_url,
                        'quantity': op.quantity
                    }
                    products_list.append(product_data)
                print(f"🔍 Fallback products_list: {len(products_list)} products")
            
            order_data = {
                'order_id': order.order_id,
                'total_amount': order.totalAmount or 0,
                'final_amount': order.final_amount or 0,
                'fname': order.fname or '',
                'lname': order.lname or '',
                'email': order.email or '',
                'mobile': order.mobile or '',
                'address': order.address or '',
                'town': order.town or '',
                'city': order.city or '',
                'state': order.state or '',
                'pincode': order.pincode or '',
                'paymentMethod': order.payment_method or 'COD',
                'payment': {
                    'method': order.payment_method or 'COD',
                    'status': order.payment_status or 'pending'
                },
                'tracking': {
                    'status': order.tracking.status if order.tracking else 'Order Placed',
                    'updatedAt': order.tracking.updatedAt.isoformat() if order.tracking and order.tracking.updatedAt else order.created_at.isoformat()
                },
                'createdAt': order.created_at.isoformat(),
                'products': products_list,
                'return_requests': [
                    {
                        'return_id': order.return_status.return_id,
                        'status': order.return_status.status,
                        'reason': order.return_status.reason,
                        'refund_amount': order.return_status.refund_amount,
                        'created_at': order.return_status.updatedAt.isoformat()
                    }
                ] if order.return_status else []
            }
            orders_data.append(order_data)
        
        return Response({
            'status': 200,
            'orders': orders_data
        })
    except Exception as e:
        return Response({
            'status': 500,
            'message': str(e)
        })

# Frontend Order APIs
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order_api(request):
    try:
        data = request.data
        print(f"🔍 DEBUG - Full order data received: {data}")
        print(f"🔍 DEBUG - Received products: {data.get('products', [])}")
        print(f"🔍 DEBUG - Products type: {type(data.get('products', []))}")
        print(f"🔍 DEBUG - Products length: {len(data.get('products', []))}")
        
        # Create address from form data if provided
        address = None
        if data.get('fname') or data.get('address'):
            try:
                address = Address.objects.create(
                    user=request.user,
                    name=f"{data.get('fname', '')} {data.get('lname', '')}".strip(),
                    phone=data.get('mobile', ''),
                    address=data.get('address', ''),
                    locality=data.get('town', ''),
                    city=data.get('city', ''),
                    state=data.get('state', ''),
                    pincode=data.get('pincode', ''),
                    landmark=''
                )
                print(f"Address created: {address.name}")
            except Exception as ae:
                print(f"Address creation error: {ae}")
        
        # Calculate amounts
        total_amount = float(data.get('totalAmount', 0))
        delivery_charges = 40 if total_amount < 500 else 0
        final_amount = total_amount + delivery_charges
        
        # Get payment method properly
        payment_method = data.get('paymentMethod', 'COD')
        if payment_method == 'cash on delivery':
            payment_method = 'COD'
        
        # Prepare complete product data for storage
        products_data = []
        print(f"Processing {len(data.get('products', []))} products for order")
        
        for product_data in data.get('products', []):
            try:
                product_id = product_data.get('_id') or product_data.get('id')
                product_name = product_data.get('product_name', '')
                
                # Try to find product by ID first
                try:
                    product = Product.objects.get(id=product_id)
                    print(f"Found product by ID {product_id}: {product.product_name}")
                except Product.DoesNotExist:
                    # Fallback: try to find by name
                    if product_name:
                        product = Product.objects.filter(product_name__icontains=product_name).first()
                        if product:
                            print(f"Found product by name '{product_name}': ID {product.id}")
                        else:
                            print(f"Product not found by name '{product_name}' either")
                            continue
                    else:
                        print(f"Product {product_id} not found and no name provided")
                        continue
                
                # Build complete product data
                complete_product_data = {
                    '_id': str(product.id),
                    'product_name': product.product_name,
                    'product_price': product.product_price,
                    'product_img': request.build_absolute_uri(product.product_img.url) if product.product_img else '',
                    'quantity': product_data.get('quantity', 1),
                    'product_return': str(product.product_return)
                }
                products_data.append(complete_product_data)
                print(f"Added product to products_data: {complete_product_data['product_name']}")
            except Exception as e:
                print(f"Error processing product {product_id}: {str(e)}")
                continue
        
        print(f"🔍 DEBUG - Final products_data array: {products_data}")
        print(f"🔍 DEBUG - Final products_data type: {type(products_data)}")
        print(f"🔍 DEBUG - Final products_data length: {len(products_data)}")
        
        # Create order WITH products_data directly
        order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            fname=data.get('fname', ''),
            lname=data.get('lname', ''),
            email=data.get('email', ''),
            mobile=data.get('mobile', ''),
            address=data.get('address', ''),
            town=data.get('town', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            pincode=data.get('pincode', ''),
            totalAmount=total_amount,
            delivery_charges=delivery_charges,
            final_amount=final_amount,
            status='confirmed' if payment_method == 'COD' else 'pending',
            payment_method=payment_method,
            payment_status='pending',
            products_data=products_data  # Direct assignment during creation
        )
        
        # Verify products_data was saved during creation
        print(f"🔍 VERIFICATION - Order created with products_data: {order.products_data}")
        print(f"🔍 VERIFICATION - Products_data length: {len(order.products_data) if order.products_data else 0}")
        
        # Set estimated delivery date
        from datetime import datetime, timedelta
        order.tracking.estimated_delivery = order.created_at + timedelta(days=5)
        order.tracking.delivery_partner = 'Bazar Express'
        if data.get('paymentMethod') == 'cash on delivery':
            order.tracking.status = 'Confirmed'
        order.tracking.save()
        
        # Create payment record
        payment_method = 'cod' if data.get('paymentMethod') == 'cash on delivery' else 'razorpay'
        payment = Payment.objects.create(
            amount=final_amount,
            method=payment_method,
            status='pending'  # Will be updated after verification
        )
        order.payment = payment
        order.save()
        
        # CRITICAL: Final verification
        order.refresh_from_db()
        print(f"🔍 FINAL CHECK - Order {order.order_id} products_data: {order.products_data}")
        print(f"🔍 FINAL CHECK - Length: {len(order.products_data) if order.products_data else 0}")
        
        # Count OrderProduct relationships as backup
        order_product_count = OrderProduct.objects.filter(order=order).count()
        print(f"🔍 FINAL CHECK - OrderProduct count: {order_product_count}")
        
        if not order.products_data or len(order.products_data) == 0:
            print("🚨 CRITICAL ERROR - Products_data still empty!")
            if order_product_count > 0:
                print(f"ℹ️ INFO - But {order_product_count} OrderProduct relationships exist as fallback")
        else:
            print(f"✅ SUCCESS - {len(order.products_data)} products saved in products_data!")
            print(f"✅ SUCCESS - {order_product_count} OrderProduct relationships also created!")
        
        # Add products to order
        received_products = data.get('products', [])
        print(f"🔍 DEBUG - About to process {len(received_products)} products for OrderProduct creation")
        
        for product_data in received_products:
            try:
                product_id = product_data.get('_id') or product_data.get('id')
                product_name = product_data.get('product_name', '')
                
                # Try to find product by ID first, then by name
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    if product_name:
                        product = Product.objects.filter(product_name__icontains=product_name).first()
                        if not product:
                            print(f"Product {product_id} ('{product_name}') not found for OrderProduct")
                            continue
                    else:
                        print(f"Product {product_id} not found for OrderProduct")
                        continue
                
                # Create OrderProduct
                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=product_data.get('quantity', 1)
                )
                
                # Create OrderItem for detailed tracking
                OrderItem.objects.create(
                    order=order,
                    product_id=str(product.id),
                    product_name=product.product_name,
                    product_price=product.product_price,
                    product_img=product_data.get('product_img', ''),
                    quantity=product_data.get('quantity', 1)
                )
                print(f"Created OrderProduct and OrderItem for: {product.product_name}")
            except Exception as e:
                print(f"Error creating OrderProduct for {product_id}: {str(e)}")
                continue
        
        # Final verification for response
        final_order = Order.objects.get(id=order.id)
        order_product_count = OrderProduct.objects.filter(order=final_order).count()
        
        return Response({
            'status': 201,
            'message': 'Order created successfully',
            'order_id': final_order.order_id,
            'payment_method': payment_method,
            'success': True,
            'debug_info': {
                'received_products_count': len(received_products),
                'processed_products_count': len(products_data),
                'saved_products_data_count': len(final_order.products_data) if final_order.products_data else 0,
                'order_product_relationships': order_product_count,
                'products_data_exists': bool(final_order.products_data and len(final_order.products_data) > 0),
                'fallback_available': order_product_count > 0
            },
            'products_data': final_order.products_data,
            'CRITICAL_SUCCESS': (final_order.products_data and len(final_order.products_data) > 0) or order_product_count > 0
        })
        
    except Exception as e:
        print(f"Order creation error: {str(e)}")
        return Response({
            'status': 500,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def check_pincode(request):
    pincode = request.data.get('pincode')
    
    # Simple pincode validation (you can add real pincode service later)
    if pincode and len(pincode) == 6 and pincode.isdigit():
        return Response({
            'status': 200,
            'msg': 'Delivery available in 3-5 days',
            'deliveryAvailable': True,
            'estimatedDays': 3
        })
    else:
        return Response({
            'status': 400,
            'msg': 'Delivery not available in this area',
            'deliveryAvailable': False,
            'estimatedDays': 0
        })

@api_view(['POST'])
def create_razorpay_order(request):
    try:
        amount = request.data.get('amount', 0)
        currency = request.data.get('currency', 'INR')
        
        print(f"Creating Razorpay order for amount: {amount}, user: {request.user if request.user.is_authenticated else 'Anonymous'}")
        
        # Create Razorpay order
        razorpay_client = get_razorpay_client()
        razorpay_order = razorpay_client.order.create({
            'amount': int(float(amount) * 100),
            'currency': currency,
            'payment_capture': 1
        })
        
        print(f"Razorpay order created: {razorpay_order['id']}")
        
        # Update latest payment record with razorpay_order_id
        try:
            # Find the latest pending payment for current user
            if request.user.is_authenticated:
                latest_order = Order.objects.filter(
                    user=request.user,
                    payment__method='razorpay',
                    payment__status='pending'
                ).latest('created_at')
                
                if latest_order and latest_order.payment:
                    latest_order.payment.razorpay_order_id = razorpay_order['id']
                    latest_order.payment.save()
                    print(f"Linked payment {latest_order.payment.id} with razorpay order {razorpay_order['id']} for order {latest_order.order_id}")
                else:
                    print("No payment found in latest order")
            else:
                print("User not authenticated, cannot link payment")
        except Order.DoesNotExist:
            print("No pending order found to link with razorpay order")
        except Exception as link_error:
            print(f"Error linking payment: {str(link_error)}")
        
        return Response({
            'key_id': settings.RAZORPAY_KEY_ID,
            'order_id': razorpay_order['id'],
            'order_amount': int(float(amount) * 100),
            'currency': currency
        })
        
    except Exception as e:
        print(f"Razorpay order error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_razorpay_payment(request):
    try:
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        print(f"Verifying payment - Order ID: {razorpay_order_id}, Payment ID: {razorpay_payment_id}")
        
        # Verify signature
        body = razorpay_order_id + "|" + razorpay_payment_id
        expected_signature = hmac.new(
            key=settings.RAZORPAY_KEY_SECRET.encode(),
            msg=body.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if expected_signature == razorpay_signature:
            # Find payment by razorpay_order_id
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'completed'
                payment.save()
                
                print(f"Payment updated to completed: {payment.id}")
                
                # Update order status
                order = payment.order
                order.status = 'confirmed'
                order.payment_status = 'completed'
                order.razorpay_payment_id = razorpay_payment_id
                order.tracking.status = 'Confirmed'
                order.tracking.save()
                order.save()
                
                print(f"Order updated to confirmed: {order.order_id}")
                
                # Update product sales count
                from django.utils import timezone
                order_products = OrderProduct.objects.filter(order=order)
                for order_product in order_products:
                    product = order_product.product
                    product.sales_count += order_product.quantity
                    product.last_sale_date = timezone.now()
                    product.save()
                
                return Response({
                    'success': True,
                    'message': 'Payment verified successfully',
                    'order_id': order.order_id,
                    'payment_status': 'completed'
                })
            except Payment.DoesNotExist:
                print(f"Payment not found for razorpay_order_id: {razorpay_order_id}")
                # Try to find by latest order for current user
                try:
                    latest_order = Order.objects.filter(
                        user=request.user if request.user.is_authenticated else None,
                        payment__method='razorpay',
                        payment__status='pending'
                    ).latest('created_at')
                    
                    if latest_order and latest_order.payment:
                        payment = latest_order.payment
                        payment.razorpay_order_id = razorpay_order_id
                        payment.razorpay_payment_id = razorpay_payment_id
                        payment.razorpay_signature = razorpay_signature
                        payment.status = 'completed'
                        payment.save()
                        
                        latest_order.status = 'confirmed'
                        latest_order.tracking.status = 'Confirmed'
                        latest_order.tracking.save()
                        latest_order.save()
                        
                        print(f"Updated latest order payment: {latest_order.order_id}")
                        
                        return Response({
                            'success': True,
                            'message': 'Payment verified successfully',
                            'order_id': latest_order.order_id
                        })
                except:
                    pass
                
                return Response({
                    'success': False,
                    'message': 'Payment record not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'Payment verification failed - Invalid signature'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"Payment verification error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Payment Success Details API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_success_details(request, order_id):
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Get order products
        order_products = OrderProduct.objects.filter(order=order)
        products_list = []
        subtotal_before_tax = 0
        
        for op in order_products:
            # Ensure proper image URL
            image_url = None
            if op.product.product_img:
                try:
                    image_url = request.build_absolute_uri(op.product.product_img.url)
                except:
                    image_url = None
            
            item_total = op.product.product_price * op.quantity
            subtotal_before_tax += item_total
            
            products_list.append({
                'id': op.product.id,
                'name': op.product.product_name,
                'title': op.product.product_titel,
                'brand': op.product.product_brand,
                'price': op.product.product_price,
                'image': image_url,
                'quantity': op.quantity,
                'total': item_total
            })
        
        # Calculate GST (18% for electronics)
        gst_rate = 18
        cgst_rate = gst_rate / 2  # 9%
        sgst_rate = gst_rate / 2  # 9%
        
        cgst_amount = (subtotal_before_tax * cgst_rate) / 100
        sgst_amount = (subtotal_before_tax * sgst_rate) / 100
        total_gst = cgst_amount + sgst_amount
        
        subtotal_with_gst = subtotal_before_tax + total_gst
        
        # Payment status
        payment_status = 'pending'
        if order.payment:
            if order.payment.method == 'cod':
                payment_status = 'pending'
            elif order.payment.method == 'razorpay':
                payment_status = 'paid' if order.payment.status == 'completed' else 'pending'
        
        success_details = {
            'order_id': order.order_id,
            'order_date': order.created_at.strftime('%d %B %Y, %I:%M %p'),
            'expected_delivery': order.tracking.estimated_delivery.strftime('%d %B %Y') if order.tracking.estimated_delivery else 'N/A',
            'tracking_id': order.tracking.tracking_id,
            'products': products_list,
            'price_breakdown': {
                'subtotal_before_tax': round(subtotal_before_tax, 2),
                'cgst': {
                    'rate': f'{cgst_rate}%',
                    'amount': round(cgst_amount, 2)
                },
                'sgst': {
                    'rate': f'{sgst_rate}%',
                    'amount': round(sgst_amount, 2)
                },
                'total_gst': round(total_gst, 2),
                'subtotal_with_gst': round(subtotal_with_gst, 2),
                'delivery_charges': order.delivery_charges,
                'final_amount': order.final_amount
            },
            'payment': {
                'method': order.payment.method.upper() if order.payment else 'COD',
                'status': payment_status,
                'amount': order.final_amount,
                'transaction_id': order.payment.razorpay_payment_id if (order.payment and order.payment.razorpay_payment_id) else None
            },
            'shipping_address': {
                'name': order.shipping_address.name if order.shipping_address else 'N/A',
                'phone': order.shipping_address.phone if order.shipping_address else 'N/A',
                'address': order.shipping_address.address if order.shipping_address else 'N/A',
                'locality': order.shipping_address.locality if order.shipping_address else 'N/A',
                'city': order.shipping_address.city if order.shipping_address else 'N/A',
                'state': order.shipping_address.state if order.shipping_address else 'N/A',
                'pincode': order.shipping_address.pincode if order.shipping_address else 'N/A',
                'full_address': f"{order.shipping_address.address}, {order.shipping_address.locality}, {order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}" if order.shipping_address else 'N/A'
            } if order.shipping_address else None
        }
        
        return Response(success_details)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Coupon APIs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_coupons(request):
    from django.utils import timezone
    coupons = Coupon.objects.filter(is_active=True, valid_till__gte=timezone.now())
    coupon_data = []
    for coupon in coupons:
        coupon_data.append({
            'id': coupon.id,
            'code': coupon.code,
            'title': coupon.title,
            'description': coupon.description,
            'discount': coupon.discount,
            'minAmount': coupon.min_amount,
            'maxDiscount': coupon.max_discount,
            'validTill': coupon.valid_till,
            'isActive': coupon.is_active
        })
    return Response({'coupons': coupon_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_coupon(request):
    try:
        coupon_code = request.data.get('code')
        cart_total = float(request.data.get('cartTotal', 0))
        
        print(f"🔍 DEBUG - Coupon Code: {coupon_code}")
        print(f"🔍 DEBUG - Cart Total: {cart_total}")
        
        if not coupon_code:
            return Response({
                'success': False,
                'message': 'Coupon code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find coupon
        from django.utils import timezone
        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                is_active=True,
                valid_till__gte=timezone.now()
            )
            print(f"🔍 DEBUG - Found Coupon: {coupon.code}")
            print(f"🔍 DEBUG - Discount Percentage: {coupon.discount}%")
            print(f"🔍 DEBUG - Min Amount: ₹{coupon.min_amount}")
            print(f"🔍 DEBUG - Max Discount: ₹{coupon.max_discount}")
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired coupon code'
            })
        
        # Check minimum amount
        if cart_total < float(coupon.min_amount):
            return Response({
                'success': False,
                'message': f'Minimum order amount should be ₹{coupon.min_amount}'
            })
        
        # Calculate discount - FIXED CALCULATION
        discount_percentage = int(coupon.discount)  # Ensure it's integer
        discount_amount = (cart_total * discount_percentage) / 100
        
        print(f"🔍 DEBUG - Discount Calculation:")
        print(f"   Cart Total: ₹{cart_total}")
        print(f"   Discount %: {discount_percentage}%")
        print(f"   Calculated Discount: ₹{discount_amount}")
        print(f"   Max Discount Limit: ₹{coupon.max_discount}")
        
        # Apply max discount limit
        if discount_amount > float(coupon.max_discount):
            discount_amount = float(coupon.max_discount)
            print(f"   Applied Max Limit: ₹{discount_amount}")
        
        final_amount = cart_total - discount_amount
        
        print(f"🔍 DEBUG - Final Calculation:")
        print(f"   Original: ₹{cart_total}")
        print(f"   Discount: ₹{discount_amount}")
        print(f"   Final: ₹{final_amount}")
        
        return Response({
            'success': True,
            'message': 'Coupon applied successfully',
            'coupon': {
                'code': coupon.code,
                'title': coupon.title,
                'discount': coupon.discount
            },
            'discount_amount': round(discount_amount, 2),
            'final_amount': round(final_amount, 2),
            'debug': {
                'cart_total': cart_total,
                'discount_percentage': discount_percentage,
                'calculated_discount': round(discount_amount, 2),
                'max_discount_limit': float(coupon.max_discount)
            }
        })
        
    except Exception as e:
        print(f"🚨 ERROR in apply_coupon: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_gift_cards(request):
    gift_cards = GiftCard.objects.filter(is_active=True)
    card_data = []
    for card in gift_cards:
        card_data.append({
            'id': card.id,
            'title': card.title,
            'description': card.description,
            'amount': card.amount,
            'image': request.build_absolute_uri(card.image.url) if card.image else None,
            'category': card.category
        })
    return Response({'giftCards': card_data})

# Music Banner API
@api_view(['GET'])
def get_music_banner(request):
    try:
        banner = MusicBanner.objects.filter(is_active=True).first()
        if banner:
            # Get banner products
            products_data = []
            for product in banner.products.all()[:6]:  # Limit to 6 products
                image_url = None
                if product.product_img:
                    try:
                        image_url = request.build_absolute_uri(product.product_img.url)
                    except:
                        image_url = None
                
                products_data.append({
                    'id': product.id,
                    'name': product.product_name,
                    'title': product.product_titel,
                    'price': product.product_price,
                    'oldPrice': product.product_oldPrice,
                    'discount': product.product_discount,
                    'brand': product.product_brand,
                    'image': image_url
                })
            
            return Response({
                'banner': {
                    'title': banner.title,
                    'subtitle': banner.subtitle,
                    'image': request.build_absolute_uri(banner.image.url) if banner.image else None,
                    'category': banner.category,
                    'priceRangeMin': banner.price_range_min,
                    'priceRangeMax': banner.price_range_max,
                    'discountText': banner.discount_text,
                    'products': products_data,
                    'isActive': banner.is_active
                }
            })
        else:
            return Response({'banner': None})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_products_by_category(request, category):
    try:
        # Search by category name, slug, or subcategory
        products = Product.objects.select_related('category', 'subcategory').filter(
            Q(category__name__icontains=category) | 
            Q(category__slug__icontains=category) |
            Q(subcategory__name__icontains=category) |
            Q(subcategory__slug__icontains=category) |
            Q(product_category__icontains=category)
        ).distinct()
        
        data = []
        for product in products:
            product_data = {
                'id': product.id,
                'product_name': product.product_name,
                'product_titel': product.product_titel,
                'product_price': product.product_price,
                'product_oldPrice': product.product_oldPrice,
                'product_discount': product.product_discount,
                'product_brand': product.product_brand,
                'product_img': request.build_absolute_uri(product.product_img.url) if product.product_img else None,
                'product_category': product.category.slug if product.category else product.product_category,
                'category': {
                    'name': product.category.name,
                    'slug': product.category.slug
                } if product.category else None,
                'subcategory': {
                    'name': product.subcategory.name,
                    'slug': product.subcategory.slug
                } if product.subcategory else None,
                'is_featured': product.is_featured,
                'is_trending': product.is_trending,
                'sales_count': product.sales_count
            }
            data.append(product_data)
        
        return Response({
            'status': 200,
            'products': data,
            'category': category,
            'total_products': len(data)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Enhanced Category APIs
@api_view(['GET'])
def get_categories(request):
    try:
        categories = Category.objects.filter(is_active=True)
        cat_data = []
        for cat in categories:
            cat_data.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'image': request.build_absolute_uri(cat.image.url) if cat.image else None,
                'description': cat.description,
                'subcategories': [
                    {
                        'id': sub.id,
                        'name': sub.name,
                        'slug': sub.slug
                    } for sub in cat.subcategories_list.filter(is_active=True)
                ]
            })
        
        return Response({
            'status': 200,
            'categories': cat_data,
            'total_categories': len(cat_data)
        })
    except Exception as e:
        return Response({
            'status': 500,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_category(request):
    try:
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 201,
                'message': 'Category added successfully',
                'category': serializer.data
            })
        return Response({
            'status': 400,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 500,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Contact APIs
@api_view(['POST'])
def submit_contact(request):
    try:
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 201,
                'message': 'Message sent successfully! We will contact you soon.'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 400,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 500,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_contacts(request):
    try:
        contacts = Contact.objects.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response({
            'status': 200,
            'contacts': serializer.data
        })
    except Exception as e:
        return Response({
            'status': 500,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Dynamic Subcategory API for Admin
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = Subcategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'subcategories': list(subcategories)})