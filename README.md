# VipraTech_Assignment - Stripe Checkout Django Shop

A minimal, interview-grade Django app that implements a **Stripe Checkout Session** payment flow with **webhook-only** order finalization.

## Assumptions

1. **Environment Setup**: Stripe API keys (publishable and secret) are configured as environment variables (`STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`).
2. **Currency**: All prices are stored in cents (USD) to avoid floating-point precision issues.
3. **User Sessions**: Orders are tracked by Stripe session ID, not by authenticated user (stateless checkout).
4. **Payment State**: Payment state is *only* updated via Stripe webhooks, never via user redirects.
5. **Fixed Products**: The shop displays 3 fixed products seeded via management command.
6. **Stripe Checkout Mode**: Using Stripe's Checkout Session API in `payment` mode (not Payment Intents).

## Flow & Architecture

### Why Stripe Checkout vs. Payment Intents?

**Chosen: Stripe Checkout Session API**

**Rationale:**
- Simpler, hosted UI reduces PCI compliance burden
- Built-in idempotency and duplicate handling at Stripe's edge
- Automatic handling of 3D Secure and payment method variety
- Lower operational overhead for a small shop
- Webhook-based confirmation is more reliable than redirect-based state changes

Payment Intents would require:
- Custom UI/form handling
- Manual PCI compliance
- More complex error recovery

For a production shop, Checkout is the safer, lower-risk choice.

### Request Flow

```
Customer              Server              Stripe
   |                   |                   |
   |---(1) Enter quantities--------------->|
   |                   |                   |
   |---(2) Click Buy---|                   |
   |                   |---(3) Create Checkout Session----->|
   |                   |<---Session ID------|
   |<---(4) Redirect to Stripe Checkout---|
   |---(5) Pay @ Stripe-------->|          |
   |                   |<--Webhook (checkout.session.completed)---|
   |                   |---(6) Mark Order PAID (idempotent)---|
   |<---(7) Refresh page, see PAID order---|
```

### Demo Mode (Default - No Keys Required)

If Stripe keys are not set, the app automatically runs in **demo mode**:
- ✅ Checkout button completes orders instantly (no Stripe API call)
- ✅ Orders appear in "My Orders" section immediately  
- ✅ Perfect for testing UI/UX without Stripe
- ✅ Database still records all transactions

**When to use demo mode:**
- Local development and testing
- Presentations and demos
- Testing the checkout flow without Stripe account

### Real Stripe Mode (When Keys Are Set)

When you set `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY`, the app automatically switches to real mode:
- 💳 Checkout redirects to Stripe's hosted checkout
- 💳 Real payment processing
- 💳 Webhook signature verification
- 💳 Orders only marked PAID after successful payment

**How it works:**
1. App starts and reads environment variables
2. `settings.py` detects both keys are present
3. `STRIPE_KEY_PRESENT = True` → `STRIPE_DEMO_MODE = False`
4. Startup logs show: `✓ Stripe keys detected. Real Stripe mode ENABLED.`
5. Checkout button now uses real Stripe Checkout Session API
6. Only webhooks can mark orders as PAID (not manual redirects)

1. Customer enters quantities and clicks **Buy**
2. Frontend POSTs `/create-checkout-session/` with `{items: [{product_id, quantity}]}` (only the 3 fixed products)
3. Server validates items, computes total, creates Stripe Checkout Session
4. Server performs an **atomic DB transaction** creating `Order(status=PENDING, session_id=<stripe_session_id>, total_cents=...)` and `OrderItem` rows
5. Frontend redirects to Stripe Checkout
6. Stripe sends `checkout.session.completed` webhook
7. Server verifies signature and marks the `Order` **PAID** (idempotent + row locked)
8. Home page shows the order in **My Orders** (PAID only)

## How Duplicate Charges Are Prevented

1. **Unique Session ID**: Each Stripe session has a globally unique ID. The `Order.session_id` field has a `unique=True` constraint, preventing database-level duplicates.

2. **Idempotent Webhook Handling**:
   - Webhook handler checks `if order.status == Order.STATUS_PAID: return 200`
   - Stripe retries webhooks if no 200 response; we safely return 200 without re-processing
   - No double charge if webhook is replayed

3. **No Redirect-Based State Changes**:
   - `success_url` redirects to home page; it does NOT mark order as PAID
   - Only the webhook handler (with verified Stripe signature) updates status
   - Prevents race conditions between success redirect and webhook arrival

4. **Atomic Database Writes**:
   - Order + OrderItems are created inside `transaction.atomic()` so we don’t end up with partial rows
   - Webhook uses `transaction.atomic()` + `select_for_update()` to avoid concurrent updates producing broken states

## Setup & Run

### Windows note (important)

On Windows, if you set env vars with `setx`, they **do not apply to the current PowerShell window**. After running `setx ...`, you must open a **new PowerShell** window before starting Django.

### Prerequisites

- Python 3.8+
- Django 4.2+
- Stripe API account (test mode keys)
- `pip` package manager
- Stripe CLI (for local webhook testing)

### Installation

```powershell
# 1) Go to the Django project
cd "d:\-VipraTech_Assignment\shop"

# 2) (Optional) Create + activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install django stripe

# 4) Apply migrations + seed the 3 fixed products
python manage.py migrate
python manage.py seed_products
```

### Configure Stripe keys (Windows PowerShell)

Persist keys (recommended):

```powershell
setx STRIPE_PUBLISHABLE_KEY "pk_test_..."
setx STRIPE_SECRET_KEY "sk_test_..."
```

Then **close PowerShell** and open a **new** PowerShell window and verify:

```powershell
echo $env:STRIPE_PUBLISHABLE_KEY
echo $env:STRIPE_SECRET_KEY
```

### Testing the App

1. Start the server:

```powershell
cd "d:\-VipraTech_Assignment\shop"
python manage.py runserver
```

2. Open `http://localhost:8000/`
2. See 3 products: Laptop ($999.99), Mouse ($29.99), Keyboard ($79.99)
3. Enter quantities and click **Buy**
4. Enter Stripe test card: 4242 4242 4242 4242 (exp: 12/34, CVC: 123)
5. On success redirect, check "My Orders" section (shows only PAID orders)

### Webhook Configuration

For local testing with Stripe webhooks:

1. In one terminal, start Django:

```powershell
cd "d:\-VipraTech_Assignment\shop"
python manage.py runserver
```

2. In a second terminal, run Stripe CLI:

```powershell
stripe listen --forward-to http://localhost:8000/stripe/webhook/
```

3. Copy the `whsec_...` printed by Stripe CLI and set it:

```powershell
setx STRIPE_WEBHOOK_SECRET "whsec_..."
```

4. Open a **new** PowerShell and verify:

```powershell
echo $env:STRIPE_WEBHOOK_SECRET
```

5. Restart Django after setting the webhook secret.

## Code Quality Notes

### Design Principles

1. **Explicit over Implicit**: All status values are class constants (`Order.STATUS_PAID`), not magic strings.
2. **Safety-First**: Webhook signature verification is mandatory; no shortcuts.
3. **Separation of Concerns**:
   - `views.index`: Fetch and display data
   - `views.create_checkout_session`: Business logic, Stripe API calls, DB writes
   - `views.stripe_webhook`: Webhook handling, idempotency checks
4. **Error Handling**: Every external API call (Stripe) is wrapped in try-except with user-friendly error messages.
5. **Stateless Design**: No session state; Order is the source of truth.

### Code Structure

- **Models** ([core/models.py](core/models.py)): 3 models (Product, Order, OrderItem) with clear docstrings.
- **Views** ([core/views.py](core/views.py)): 3 pure functions (no classes), ~170 LOC, well-commented.
- **URLs** ([core/urls.py](core/urls.py)): Named routes for reverse URL generation.
- **Template** ([core/templates/core/index.html](core/templates/core/index.html)): Clean HTML5, inline Stripe.js, client-side cart with basic UX polish.
- **Management Command** ([core/management/commands/seed_products.py](core/management/commands/seed_products.py)): Idempotent seeding, bulk insert.

### Security

- CSRF protection enabled (default Django; exempted only for webhook)
- Stripe signature verification on all webhooks
- No hardcoded secrets; environment variables only
- Price validation server-side (client cart is for UX only)

### Performance

- Database queries are optimized (`prefetch_related` for order items)
- No N+1 queries in views
- Stripe session creation is the only I/O; is O(1) per cart

### Testing

Manual testing sufficient for MVP. For production, add:
- Unit tests for `create_checkout_session` (mock Stripe)
- Unit tests for webhook handler (idempotency, signature verification)
- Integration tests (full flow with Stripe test keys)

## Time Spent

**Estimated:** [PLACEHOLDER - to be filled with actual implementation time]

