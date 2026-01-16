# Windows PowerShell: Setting Up Stripe Keys

This guide addresses the critical configuration requirement for Windows users to enable real Stripe mode in the Django shop application.

## The Core Issue

On Windows, environment variables set with `setx` **do NOT apply to the current PowerShell session**. They only apply to **new** sessions opened after the `setx` command.

This causes a common scenario:
1. You run `setx STRIPE_SECRET_KEY "sk_test_xxx"`
2. You continue in the same PowerShell window
3. The Django server doesn't detect the key (because current session doesn't have it yet)
4. App stays in demo mode
5. **You think Stripe configuration is broken** ❌

**The solution:** Open a **NEW PowerShell window** after running `setx`.

## Why the App Stays in Demo Mode

The Django app has intelligent auto-detection:

```python
# In settings.py
STRIPE_KEY_PRESENT = bool(STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY)
STRIPE_DEMO_MODE = not STRIPE_KEY_PRESENT
```

If environment variables aren't visible to Python when settings.py is loaded, the app assumes keys are missing and activates demo mode. **This is correct behavior** - the keys genuinely aren't available in that session.

## Step-by-Step: Correct Windows Setup

### Step 1: Get Your Stripe Keys

Log into [Stripe Dashboard](https://dashboard.stripe.com/apikeys) and copy:
- **Publishable key** (starts with `pk_test_` or `pk_live_`)
- **Secret key** (starts with `sk_test_` or `sk_live_`)

### Step 2: Open a NEW PowerShell Window

**CRITICAL**: Do NOT use the current window. Open Windows menu and launch PowerShell fresh, or:

```powershell
# From current window, you can start a new one, but then you'll need to open another
start powershell
```

### Step 3: Run `setx` Commands in the NEW Window

In the fresh PowerShell window, run:

```powershell
# Set publishable key
setx STRIPE_PUBLISHABLE_KEY "pk_test_YOUR_KEY_HERE"

# Set secret key  
setx STRIPE_SECRET_KEY "sk_test_YOUR_KEY_HERE"

# Optional: Set webhook secret if using webhooks
setx STRIPE_WEBHOOK_SECRET "whsec_YOUR_WEBHOOK_SECRET"
```

**Replace** `YOUR_KEY_HERE` with your actual keys from Stripe Dashboard.

### Step 4: OPEN ANOTHER NEW PowerShell Window

This is the critical step many users miss. Run `setx` in one window, then open **yet another** new window.

In this newest window, verify the keys are now visible:

```powershell
echo $env:STRIPE_PUBLISHABLE_KEY
echo $env:STRIPE_SECRET_KEY
```

You should see your actual keys printed. If empty, the `setx` command didn't work - go back to Step 3 and try again as Administrator.

### Step 5: Start Django Server in THIS Window

In the same PowerShell window where you just verified the keys:

```powershell
cd d:\-VipraTech_Assignment\shop
python manage.py runserver 0.0.0.0:8000
```

### Step 6: Verify Real Mode Activation

When the server starts, check the console output. You should see:

```
✓ Stripe keys detected. Real Stripe mode ENABLED.
```

If you see instead:

```
⚠ Stripe keys not detected. Demo mode ENABLED.
```

Then go back to Step 4 and verify the keys are visible with `echo`.

---

## Testing Real Stripe Mode

Once you see "Real Stripe mode ENABLED" in the logs:

1. Visit **http://localhost:8000**
2. Add products to cart
3. You should see a "Checkout with Stripe" button
4. Click to enter Stripe's hosted checkout
5. Use Stripe test card: **4242 4242 4242 4242**
6. Use any future expiry date and any 3-digit CVC

If checkout completes successfully, real Stripe mode is working!

---

## Command Reference: PowerShell Window Lifecycle

```powershell
# Window A (original):
setx STRIPE_SECRET_KEY "sk_test_xxx"  
# Variables NOT visible in Window A yet

# Window B (new - maybe from Start menu):
echo $env:STRIPE_SECRET_KEY          # Variables visible!

# Window C (another new window):
echo $env:STRIPE_SECRET_KEY          # Still visible, can be any new window after setx
```

The key point: **After `setx`, variables are visible in all NEW PowerShell windows, but not the one where you ran `setx`.**

---

## Troubleshooting

### "Keys still showing as empty"

**Checklist:**
1. Are you in a **brand new** PowerShell window? (If unsure, open Windows menu and click PowerShell)
2. Is the `setx` command actually running? (Should show success message)
3. Try running as Administrator: Right-click PowerShell → "Run as Administrator"
4. After `setx`, try typing `whoami` to verify you have proper permissions

### "Real mode still not enabling"

1. Verify keys ARE visible: `echo $env:STRIPE_SECRET_KEY`
2. Stop Django server (Ctrl+C)
3. Restart Django server in the same window: `python manage.py runserver`
4. Check startup logs again for "Real Stripe mode ENABLED"
5. Check console for any Python errors

### "I set STRIPE_DEMO_MODE=true but it's not working"

The app will ignore `STRIPE_DEMO_MODE` if keys are present. If you want to force demo mode:

```powershell
setx STRIPE_SECRET_KEY ""
setx STRIPE_PUBLISHABLE_KEY ""
```

Then open a new window and restart Django.

---

## How It Works: The Auto-Detection Logic

When Django starts, it reads `settings.py` which contains:

```python
import os

# Read from environment (returns empty string if not found)
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# Check if both keys are present and non-empty
STRIPE_KEY_PRESENT = bool(STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY)

# Auto-select mode: Real mode if keys present, Demo mode if not
STRIPE_DEMO_MODE = not STRIPE_KEY_PRESENT

# Optional: User can explicitly override via environment variable
if 'STRIPE_DEMO_MODE' in os.environ:
    override_value = os.environ.get('STRIPE_DEMO_MODE', '').lower()
    STRIPE_DEMO_MODE = override_value in ('true', '1', 'yes')
```

This logic means:
- ✅ No keys detected → Demo mode automatically enabled
- ✅ Both keys present → Real mode automatically enabled
- ✅ User can manually override with `setx STRIPE_DEMO_MODE true` if needed

The app will **always** work - either in demo mode (instant order completion) or real mode (actual Stripe checkout). You don't need to configure anything else!

---

## Summary

**The single most important thing:** After running `setx`, open a **NEW PowerShell window** to verify the variables are visible, then start Django.

The app's auto-detection will handle the rest automatically.

If you follow these steps exactly, you'll see "Real Stripe mode ENABLED" in the logs and the checkout button will work with real Stripe. 🎉
