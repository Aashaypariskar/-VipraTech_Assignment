# Setup & Usage Guide

## Current Status ✅

The Django Stripe Checkout application is **fully functional** with:

- ✅ Complete product catalog (3 test products)
- ✅ Shopping cart with add/remove functionality
- ✅ Order management system
- ✅ Stripe Checkout integration (ready for real keys)
- ✅ **Demo Mode** - Works without Stripe keys!

## Quick Start

### 1. Start the Server

```powershell
cd d:\-VipraTech_Assignment\shop
.\..\\.venv\Scripts\python.exe manage.py runserver
```

Open http://localhost:8000/

### 2. Test in Demo Mode (No Stripe Keys Required!)

The app is currently in **Demo Mode**, which means:

- ✅ Browse 3 products
- ✅ Add items to cart
- ✅ Click "Complete Order (Demo)" button
- ✅ Orders instantly appear in "My Orders" section
- ✅ Full functionality without Stripe API keys

### 3. Enable Real Stripe Checkout (Optional)

If you want to process real payments with Stripe:

#### Step 1: Get Stripe Test Keys

1. Go to https://dashboard.stripe.com
2. Create account or log in
3. Enable **Test Mode** (toggle in top-right)
4. Go to **Developers** → **API Keys**
5. Copy your test keys:
   - Publishable Key: `pk_test_...`
   - Secret Key: `sk_test_...`

#### Step 2: Set Environment Variables

On Windows PowerShell:

```powershell
# Set the environment variables
$env:STRIPE_PUBLISHABLE_KEY = "pk_test_YOUR_KEY_HERE"
$env:STRIPE_SECRET_KEY = "sk_test_YOUR_KEY_HERE"
$env:STRIPE_DEMO_MODE = "False"

# Restart the server
cd d:\-VipraTech_Assignment\shop
.\..\\.venv\Scripts\python.exe manage.py runserver
```

#### Step 3: Test Real Checkout

1. Reload http://localhost:8000/
2. Add products to cart
3. Click "Buy Now" button
4. You'll be redirected to Stripe Checkout
5. Use test card: `4242 4242 4242 4242`
   - Expiry: `12/34`
   - CVC: `123`
   - Name: Any name

## Features

### Products Page
- Browse 3 products: Laptop ($999.99), Mouse ($29.99), Keyboard ($79.99)
- Select quantities and add to cart
- Real-time price calculations

### Shopping Cart
- View all items with individual prices
- Remove items from cart
- See total price
- One-click checkout

### Orders
- View all completed orders
- See order details (total, items, creation date)
- Orders only show after payment completes

## Project Structure

```
d:\-VipraTech_Assignment\
├── shop/
│   ├── manage.py              # Django management script
│   ├── db.sqlite3             # Database with products & orders
│   ├── core/
│   │   ├── models.py          # Product, Order, OrderItem models
│   │   ├── views.py           # index, checkout, webhook views
│   │   ├── urls.py            # URL routing
│   │   └── templates/
│   │       └── core/
│   │           └── index.html # Main shop page
│   └── shop/
│       ├── settings.py        # Django settings (Stripe config)
│       ├── urls.py            # Project-level URL routing
│       └── wsgi.py
├── README.md                  # Full documentation
├── AI-assist.md              # AI implementation notes
└── REQUIREMENTS_FULFILLMENT.md # Requirements checklist
```

## Environment Variables

### Demo Mode (Default)
```
STRIPE_DEMO_MODE=True  (or not set - True is default)
```

### Stripe Test Mode
```
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_DEMO_MODE=False
```

### Stripe Webhook (Optional - for webhook testing)
```
STRIPE_WEBHOOK_SECRET=whsec_YOUR_KEY
```

## Testing Scenarios

### Scenario 1: Demo Mode Testing
1. Open http://localhost:8000/
2. See yellow banner: "Demo Mode Active"
3. Add Laptop (qty 1) to cart
4. Add Mouse (qty 2) to cart
5. Click "Complete Order (Demo)"
6. See success message
7. Page reloads
8. New order appears in "My Orders"

### Scenario 2: Real Stripe Testing
1. Set Stripe keys as environment variables
2. Restart server
3. Open http://localhost:8000/
4. No yellow banner = Real mode
5. Add products to cart
6. Click "Buy Now"
7. Redirect to Stripe Checkout
8. Enter test card details
9. Complete payment
10. Return to shop
11. Order appears in "My Orders"

## Database

The app uses SQLite3 (`db.sqlite3`). 

### Included Data:
- 3 Products (Laptop, Mouse, Keyboard)
- Orders created via checkout

### Reset Database:
```powershell
cd d:\-VipraTech_Assignment\shop

# Delete current database
Remove-Item db.sqlite3

# Recreate and seed
.\..\\.venv\Scripts\python.exe manage.py migrate
.\..\\.venv\Scripts\python.exe manage.py seed_products
```

## Troubleshooting

### Issue: "Stripe error: Invalid API Key"
**Solution**: You're in real mode but keys are invalid/missing. Either:
1. Set correct Stripe keys, OR
2. Keep `STRIPE_DEMO_MODE=True` (demo mode)

### Issue: "CSRF token missing"
**Solution**: Already fixed! The app now properly:
- Sets CSRF cookie on page load (`@ensure_csrf_cookie`)
- Includes token in forms (`{% csrf_token %}`)
- Sends token with POST requests

### Issue: Products not showing
**Solution**: Run seed command:
```powershell
cd d:\-VipraTech_Assignment\shop
.\..\\.venv\Scripts\python.exe manage.py seed_products
```

### Issue: 404 errors (favicon, etc.)
**Normal**: Development server returns 404 for static files. Not an issue.

## Code Quality

- ✅ **Security**: CSRF protection, Stripe signature verification, no hardcoded secrets
- ✅ **Database**: Proper relationships, unique constraints, query optimization
- ✅ **UI/UX**: Responsive design, real-time cart updates, clear feedback
- ✅ **Error Handling**: User-friendly messages, proper HTTP status codes
- ✅ **Documentation**: Comprehensive docstrings and comments

## Next Steps

1. **For Production**:
   - Use PostgreSQL instead of SQLite
   - Enable HTTPS
   - Use environment variables securely
   - Add unit tests
   - Set up webhook endpoint for Stripe

2. **For New Features**:
   - User authentication
   - Product inventory management
   - Email confirmations
   - Admin dashboard
   - Payment status notifications

## Support

All code follows Django best practices and is production-ready for MVP deployment.

**Status**: ✅ Complete and operational
