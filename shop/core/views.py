from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Product, Order, OrderItem


def index(request):
    """
    Display the home page with product list and order history.
    
    Flow:
    1. Fetch all products from database
    2. Fetch orders for current session/user
    3. Render index.html with products and orders
    
    TODO: Implement logic to fetch products and orders
    """
    # TODO: Fetch products from Product model
    # TODO: Fetch orders from Order model
    # TODO: Pass data to template
    pass


@require_http_methods(["POST"])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for the cart.
    
    Flow:
    1. Parse cart items from request
    2. Validate cart contents
    3. Create Order and OrderItem records
    4. Initialize Stripe checkout session
    5. Return session ID to frontend
    
    TODO: Implement Stripe session creation
    """
    # TODO: Parse cart items from request body
    # TODO: Validate product availability and quantities
    # TODO: Create Order instance
    # TODO: Create OrderItem instances for each cart item
    # TODO: Call Stripe API to create checkout session
    # TODO: Return session ID as JSON
    pass


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events for payment confirmation.
    
    Flow:
    1. Verify webhook signature from Stripe
    2. Parse webhook event payload
    3. Check for checkout.session.completed event
    4. Update Order status to completed
    5. Return success response
    
    TODO: Implement Stripe webhook verification and handling
    """
    # TODO: Get webhook signature from request headers
    # TODO: Verify signature using Stripe library
    # TODO: Parse JSON payload from request body
    # TODO: Extract event type and session ID
    # TODO: Find corresponding Order by session ID
    # TODO: Update Order status to 'completed'
    # TODO: Return 200 response to Stripe
    pass
