import json
import stripe
import logging
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.conf import settings
from django.db import transaction, IntegrityError

from .models import Product, Order, OrderItem

logger = logging.getLogger(__name__)

# Initialize Stripe API key (real mode when keys exist)
stripe.api_key = settings.STRIPE_SECRET_KEY if settings.STRIPE_KEY_PRESENT else None


@ensure_csrf_cookie
def index(request):
    """
    Display the home page with product list and order history.
    
    Flow:
    1. Fetch all products from database
    2. Fetch PAID orders only
    3. Render index.html with products and orders
    4. Determine Stripe mode based on key presence
    """
    # Display exactly 3 fixed products (seeded deterministically).
    products = list(Product.objects.order_by('id')[:3])
    for p in products:
        p.price_display = f"{p.price_cents / 100:.2f}"

    paid_orders = list(
        Order.objects.filter(status=Order.STATUS_PAID).prefetch_related('items__product')
    )
    for o in paid_orders:
        o.total_display = f"{o.total_cents / 100:.2f}"
    
    # Stripe mode is determined by key presence
    stripe_configured = settings.STRIPE_KEY_PRESENT
    demo_mode = settings.STRIPE_DEMO_MODE
    
    return render(request, 'core/index.html', {
        'products': products,
        'orders': paid_orders,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY if stripe_configured else 'pk_demo_mode',
        'stripe_configured': stripe_configured,
        'demo_mode': demo_mode,
    })


@require_http_methods(["POST"])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for the cart.
    
    Flow:
    1. Parse cart items from request body (JSON)
    2. Validate products exist and quantities are positive
    3. Calculate total in cents
    4. Create Stripe checkout session (test mode) OR demo session
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
        
        # Allow only the 3 fixed products displayed on the page.
        allowed_products = list(Product.objects.order_by('id')[:3])
        allowed_by_id = {p.id: p for p in allowed_products}

        # Validate and collect line items for Stripe/demo
        line_items = []
        total_cents = 0
        order_items = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if not isinstance(product_id, int):
                return JsonResponse({'error': 'Invalid product_id'}, status=400)
            if not isinstance(quantity, int) or quantity < 0:
                return JsonResponse({'error': f'Invalid quantity for product {product_id}'}, status=400)
            if quantity == 0:
                continue

            product = allowed_by_id.get(product_id)
            if product is None:
                return JsonResponse({'error': f'Product {product_id} not found'}, status=400)
            
            # Calculate cost
            item_total = product.price_cents * quantity
            total_cents += item_total
            
            # Add to line items (for both Stripe and demo)
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
            
            order_items.append((product, quantity))

        if not line_items:
            return JsonResponse({'error': 'Please select at least one item'}, status=400)
        
        # Check if Stripe is configured based on key presence flag from settings
        if settings.STRIPE_DEMO_MODE or not settings.STRIPE_KEY_PRESENT:
            # Demo mode (fallback only): create order as PAID immediately (no Stripe call).
            demo_session_id = f"demo_{uuid.uuid4().hex}"
            with transaction.atomic():
                order = Order.objects.create(
                    session_id=demo_session_id,
                    status=Order.STATUS_PAID,
                    total_cents=total_cents,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=product, quantity=qty)
                    for (product, qty) in order_items
                ])
            return JsonResponse({'sessionId': order.session_id, 'demo': True})

        # Real Stripe mode: Create Stripe checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                # Redirect is NOT used to mark orders paid; webhook is the only source of truth.
                success_url=request.build_absolute_uri('/') + '?success=1&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/') + '?canceled=1',
            )
        except stripe.error.AuthenticationError:
            return JsonResponse(
                {'error': 'Stripe API key is invalid. Please configure STRIPE_SECRET_KEY.'},
                status=500,
            )
        except stripe.error.StripeError as e:
            return JsonResponse({'error': f'Stripe error: {str(e)}'}, status=500)

        # Atomic DB writes: create Order + OrderItems together.
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    session_id=session.id,
                    status=Order.STATUS_PENDING,
                    total_cents=total_cents,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=product, quantity=qty)
                    for (product, qty) in order_items
                ])
        except IntegrityError:
            return JsonResponse({'error': 'Duplicate checkout session. Please retry.'}, status=409)

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
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error('STRIPE_WEBHOOK_SECRET is not configured.')
        return JsonResponse({'error': 'Webhook secret not configured'}, status=500)

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
            with transaction.atomic():
                order = Order.objects.select_for_update().get(session_id=session_id)

                # Idempotent: if already PAID, return 200
                if order.status == Order.STATUS_PAID:
                    return JsonResponse({'status': 'success'})

                order.status = Order.STATUS_PAID
                order.save(update_fields=['status'])
        except Order.DoesNotExist:
            # Don't ask Stripe to retry forever; log for investigation.
            logger.warning('Webhook for unknown session_id=%s', session_id)
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'success'})


@require_http_methods(["GET"])
def order_status(request):
    """
    Read-only endpoint used by the frontend after Stripe redirect.

    This does NOT mark anything as PAID; it only reports what the webhook has finalized.
    """
    session_id = request.GET.get('session_id', '')
    if not session_id:
        return JsonResponse({'error': 'Missing session_id'}, status=400)

    try:
        order = Order.objects.only('status').get(session_id=session_id)
    except Order.DoesNotExist:
        # Session exists at Stripe but order creation could have failed; treat as pending.
        return JsonResponse({'status': 'PENDING'})

    return JsonResponse({'status': order.status})
