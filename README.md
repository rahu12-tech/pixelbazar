# Bazar Backend - E-commerce API

Complete e-commerce backend with Flipkart-like functionality including product management, cart, wishlist, checkout, payment integration, order tracking, and return/refund system.

## Features

- 🛍️ **Product Management** - Browse, search products
- 🛒 **Shopping Cart** - Add, update, remove items
- ❤️ **Wishlist** - Save favorite products
- 📍 **Address Management** - Multiple delivery addresses
- 💳 **Payment Integration** - Razorpay & COD
- 📦 **Order Management** - Order history, tracking
- 🔄 **Return/Refund** - Complete return process
- 🚚 **Delivery Tracking** - Real-time order status

## API Endpoints

### Products
```
GET /api/products/ - Get all products
GET /api/products/{id}/ - Get product details
GET /api/products/search/?q=query - Search products
```

### Cart Management
```
GET /api/cart/ - Get cart items
POST /api/cart/add/ - Add to cart
PUT /api/cart/{id}/update/ - Update quantity
DELETE /api/cart/{id}/remove/ - Remove item
```

### Wishlist
```
GET /api/wishlist/ - Get wishlist
POST /api/wishlist/add/ - Add to wishlist
DELETE /api/wishlist/{id}/remove/ - Remove from wishlist
```

### Address Management
```
GET /api/addresses/ - Get user addresses
POST /api/addresses/add/ - Add new address
PUT /api/addresses/{id}/update/ - Update address
DELETE /api/addresses/{id}/delete/ - Delete address
```

### Checkout & Payment
```
POST /api/checkout/create-order/ - Create order
POST /api/payment/verify/ - Verify Razorpay payment
```

### Order Management
```
GET /api/orders/ - Get order history
GET /api/orders/{order_id}/ - Get order details
GET /api/orders/{order_id}/track/ - Track order
POST /api/orders/{order_id}/cancel/ - Cancel order
```

### Return & Refund
```
POST /api/orders/{order_id}/return/ - Request return
GET /api/returns/{return_id}/status/ - Check return status
```

## Setup Instructions

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Environment Setup**
```bash
cp .env.example .env
# Update .env with your credentials
```

3. **Database Migration**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create Superuser**
```bash
python manage.py createsuperuser
```

5. **Run Server**
```bash
python manage.py runserver
```

## Razorpay Integration

### Frontend Integration Example
```javascript
// Create Order
const orderResponse = await fetch('/api/checkout/create-order/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        address_id: selectedAddressId,
        payment_method: 'razorpay'
    })
});

const orderData = await orderResponse.json();

// Initialize Razorpay
const options = {
    key: orderData.key,
    amount: orderData.amount * 100,
    currency: orderData.currency,
    order_id: orderData.razorpay_order_id,
    handler: async function(response) {
        // Verify payment
        await fetch('/api/payment/verify/', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
            })
        });
    }
};

const rzp = new Razorpay(options);
rzp.open();
```

## Order Status Flow

1. **Order Placed** → 2. **Confirmed** → 3. **Packaging** → 4. **Shipped** → 5. **Out for Delivery** → 6. **Delivered**

## Return Process

1. **Request Return** → 2. **Return Approved** → 3. **Picked Up** → 4. **Refund Initiated** → 5. **Refund Completed**

## Authentication

All protected endpoints require JWT token in header:
```
Authorization: Bearer <your-jwt-token>
```

## Error Handling

API returns standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Server Error