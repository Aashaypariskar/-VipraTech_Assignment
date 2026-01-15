You are my senior Django engineer.

Goal: Generate the full project skeleton for a Stripe Checkout based Django app.

DO NOT implement business logic yet.
Instead:

- Populate every file with:
  - correct imports
  - function/class definitions
  - docstrings explaining intent
  - TODO markers where logic will go

Files to fill:

core/models.py
- Define Product, Order, OrderItem models exactly as per spec.
- Add comments explaining each field.

core/views.py
- Define:
  - index(request)
  - create_checkout_session(request)
  - stripe_webhook(request)
- Each function should contain:
  - docstring describing flow
  - TODO blocks for logic

core/urls.py
- Map routes for:
  - /
  - /create-checkout-session/
  - /stripe/webhook/

shop/urls.py
- Include core.urls

core/templates/index.html
- Basic HTML structure:
  - Product list section
  - Quantity inputs
  - Buy button
  - “My Orders” section
- Use placeholders and HTML comments for dynamic parts.

core/management/commands/seed_products.py
- Create a management command skeleton
- Include TODO to insert exactly 3 products

Rules:
- No Stripe code yet
- No business logic yet
- This pass is ONLY structure + intent
- Every file must be syntactically valid Python/HTML
- Use clear comments and TODOs

The result must be a runnable Django project skeleton.

