import json
import stripe
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Product, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


@ensure_csrf_cookie
def index(request):
    """
    Display the home page with product list and order history.
    
    Flow:
    1. Fetch all products from database
    2. Fetch PAID orders only
    3. Render index.html with products and orders
    """
    products = Product.objects.all()
    paid_orders = Order.objects.filter(status=Order.STATUS_PAID).prefetch_related('items__product')
    
    return render(request, 'core/index.html', {
        'products': products,
        'orders': paid_orders,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@require_http_methods(["POST"])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for the cart.
    
    Flow:
    1. Parse cart items from request body (JSON)
    2. Validate products exist and quantities are positive
    3. Calculate total in cents
    4. Create Stripe checkout session (test mode)
    5. Create Order with status=PENDING and session_id from Stripe
    6. Create OrderItem rows for each product
    7. Return session ID (frontend redirects to Stripe)
    
    Error Handling:
    - Return 400 if product not found or invalid quantity
    - Return 500 if Stripe API fails
    """
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({'error': 'No items in cart'}, status=400)
        
        # Validate and collect line items for Stripe
        line_items = []
        total_cents = 0
        order_items_data = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            # Validate quantity
            if not isinstance(quantity, int) or quantity <= 0:
                return JsonResponse({'error': f'Invalid quantity for product {product_id}'}, status=400)
            
            # Fetch product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'error': f'Product {product_id} not found'}, status=400)
            
            # Calculate cost
            item_total = product.price_cents * quantity
            total_cents += item_total
            
            # Add to Stripe line items
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': product.price_cents,
                },
                'quantity': quantity,
            })
            
            order_items_data.append({
                'product': product,
                'quantity': quantity,
            })
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/'),
            cancel_url=request.build_absolute_uri('/'),
        )
        
        # Create Order with PENDING status
        order = Order.objects.create(
            session_id=session.id,
            status=Order.STATUS_PENDING,
            total_cents=total_cents,
        )
        
        # Create OrderItems
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
            )
        
        return JsonResponse({'sessionId': session.id})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({'error': f'Stripe error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events for payment confirmation.
    
    Flow:
    1. Verify webhook signature from request headers using Stripe library
    2. Parse JSON payload from request body
    3. Check event type for 'checkout.session.completed'
    4. Extract session_id from event
    5. Fetch Order by session_id
    6. If Order status is already PAID, return 200 (idempotent)
    7. Else update Order status to PAID
    8. Return 200 response to Stripe
    
    Safety:
    - Uses unique session_id to prevent double charges
    - Idempotent: checking existing PAID status prevents re-processing
    - Webhook only source of truth for payment (never via redirect)
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session['id']
        
        try:
            order = Order.objects.get(session_id=session_id)
            
            # Idempotent: if already PAID, return 200
            if order.status == Order.STATUS_PAID:
                return JsonResponse({'status': 'success'})
            
            # Mark order as PAID
            order.status = Order.STATUS_PAID
            order.save(update_fields=['status'])
        
        except Order.DoesNotExist:
            # Session ID not found in database
            return JsonResponse({'error': 'Order not found'}, status=404)
    
    return JsonResponse({'status': 'success'})
