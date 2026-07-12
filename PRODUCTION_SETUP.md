# 🚀 PRODUCTION SETUP - REAL UK CARD CHARGES

## STEP 1: Get Real Razorpay Account (Production)

### 1A. Create Razorpay Business Account

1. Go to https://razorpay.com
2. Click **Sign Up**
3. Choose: **Business Account**
4. Enter business details:
   - Business Name
   - Email
   - Phone
   - Country: **United Kingdom**
5. Complete KYC verification
   - PAN/VAT number
   - Bank account details
   - Business address

### 1B. Complete Activation

1. Razorpay will verify your business (1-3 days)
2. You'll get approval email
3. Activate account in dashboard

---

## STEP 2: Get Real API Keys (Production)

### In Razorpay Dashboard

1. Login to https://dashboard.razorpay.com (with production account)
2. Go to **Settings → API Keys**
3. You'll see TWO sets of keys:
   - **Test Keys** (for testing, no charges)
   - **Live Keys** (REAL CHARGES, REAL MONEY)
4. Copy **LIVE Key ID** and **LIVE Key Secret**
5. **NEVER** share these keys publicly

---

## STEP 3: Setup Payment Webhook

### 3A. Create Webhook in Razorpay

1. Dashboard → Settings → Webhooks
2. Add webhook endpoint: `https://your-bot-domain.com/webhook/razorpay`
3. Select events:
   - ✅ payment.authorized
   - ✅ payment.failed
   - ✅ payment.captured
4. Copy webhook secret

### 3B. Configure Bot to Handle Webhooks

Your bot needs to listen for payment confirmations and add credits automatically.

---

## STEP 4: Set Railway Environment Variables

### In Railway Dashboard

1. Go to your project
2. Select `telegram-checker-bot` service
3. Click **Variables** tab
4. Set these variables:

```
BOT_TOKEN = your_telegram_bot_token

RAZORPAY_KEY_ID = rzp_live_xxxxxxxxxxxxx  # From Live Keys
RAZORPAY_KEY_SECRET = xxxxxxxxxxxxxxxx   # From Live Keys

RAZORPAY_WEBHOOK_SECRET = xxxxxxxx       # From Webhook settings

ENVIRONMENT = production
```

**⚠️ CRITICAL: Use LIVE keys, NOT test keys for real charges**

---

## STEP 5: Payment Flow (Production)

### User wants Premium (₹499)

```
User clicks: [⭐ Premium - ₹499]
    ↓
Bot creates Razorpay order:
  amount: 49900 paise (₹499)
  currency: INR
  receipt: user_123456_plan_premium
    ↓
User sees Razorpay payment page:
  [Enter Card Details]
  Card: 4111111111111111
  Expiry: 12/25
  CVV: 123
    ↓
User clicks: Pay Now
    ↓
REAL MONEY CHARGED FROM CARD
    ↓
Razorpay sends webhook to your bot:
  event: payment.captured
  payment_id: pay_xxxxx
  order_id: order_xxxxx
  amount: 49900
    ↓
Bot receives webhook:
  Verify signature (HMAC-SHA256)
  Add 5000 credits to user
  Update payment status in database
    ↓
User gets confirmation:
✅ Payment successful
💳 5000 credits added
```

---

## STEP 6: Testing Before Going Live

### 6A. Test with Razorpay Test Keys (FREE)

```
RAZORPAY_KEY_ID = rzp_test_xxxxxxxxxxxxx  # Test Key
RAZORPAY_KEY_SECRET = xxxxxxxxxxxxxxxx   # Test Secret
```

**Test Cards (NO REAL CHARGES):**
```
Success:  4111111111111111 | 12/25 | 123
Decline:  4000000000000002 | 12/25 | 123
Timeout:  4000000000000341 | 12/25 | 123
```

### 6B. Switch to Live Keys (REAL CHARGES)

When ready for production:
```
RAZORPAY_KEY_ID = rzp_live_xxxxxxxxxxxxx  # LIVE Key
RAZORPAY_KEY_SECRET = xxxxxxxxxxxxxxxx   # LIVE Secret
```

**Real Cards to Accept:**
```
All UK credit/debit cards
All international cards
3D Secure enabled
```

---

## STEP 7: UK Card Charges Setup

### Payment Processing

✅ **Accepted Currencies:** GBP, INR, USD
✅ **Accepted Cards:** Visa, Mastercard, Amex (all UK banks)
✅ **Settlement:** To your UK bank account
✅ **Fees:** 2-3% + fixed fee per transaction

### UK-Specific Setup

1. **Bank Account:** UK current account
2. **Tax ID:** VAT number (if applicable)
3. **Currency:** Choose INR or GBP
4. **Settlement Account:** Link UK bank

### Charges Breakdown (Example: ₹499)

```
User pays:     ₹499
Razorpay fee:  -₹15 (3%)
You receive:   ₹484

For GBP equivalent (~£5):
User pays:     £5.00
Razorpay fee:  -£0.15
You receive:   £4.85
```

---

## STEP 8: Payment Handling in Code

### Updated handlers/payment.py (Production)

```python
# When user clicks "Premium Plan"
async def payment_callback(callback, db, state):
    plan = PLANS["plan_premium"]
    user_id = callback.from_user.id
    
    # Create Razorpay order with LIVE account
    order = client.order.create({
        "amount": 49900,  # ₹499 in paise
        "currency": "INR",
        "receipt": f"user_{user_id}_premium",
        "payment_capture": 1,  # Auto-capture payment
        "notes": {
            "user_id": user_id,
            "plan": "premium"
        }
    })
    
    # Show Razorpay payment link
    payment_link = generate_razorpay_payment_link(order["id"])
    
    await callback.message.edit_text(
        f"💳 Payment Link:\n\n"
        f"{payment_link}\n\n"
        f"Click to pay ₹499 securely"
    )
```

### Webhook Handler (receives payment confirmation)

```python
@app.post("/webhook/razorpay")
async def razorpay_webhook(request):
    # Verify webhook signature
    signature = request.headers.get("X-Razorpay-Signature")
    body = await request.body()
    
    # Verify with HMAC-SHA256
    is_valid = verify_signature(body, signature, WEBHOOK_SECRET)
    
    if not is_valid:
        return {"error": "Invalid signature"}, 400
    
    # Parse webhook data
    data = json.loads(body)
    event = data["event"]  # "payment.captured"
    
    if event == "payment.captured":
        payment_id = data["payload"]["payment"]["entity"]["id"]
        order_id = data["payload"]["payment"]["entity"]["order_id"]
        amount = data["payload"]["payment"]["entity"]["amount"]  # in paise
        user_id = data["payload"]["payment"]["entity"]["notes"]["user_id"]
        
        # Add credits to user
        db.update_credits(user_id, 5000)
        db.confirm_payment(payment_id)
        
        # Notify user in Telegram
        await bot.send_message(
            user_id,
            f"✅ Payment Successful!\n\n"
            f"💳 ₹{amount/100} charged\n"
            f"💎 5000 credits added\n\n"
            f"Start checking cards now!"
        )
    
    return {"status": "ok"}
```

---

## STEP 9: Real Card Testing (UK Users)

### Test with Real UK Cards (Small Amount)

Before charging users ₹499, test with:
- Your own UK bank card
- Charge small amount (₹1-10)
- Verify payment successful
- Check credits added
- Check UK bank received payment

### Countries That Can Use It

✅ India (INR)
✅ UK (GBP/INR)
✅ USA (USD)
✅ All Razorpay supported countries

---

## STEP 10: Security for Production

### API Keys Protection

```
❌ NEVER push to GitHub:
- RAZORPAY_KEY_ID
- RAZORPAY_KEY_SECRET
- RAZORPAY_WEBHOOK_SECRET

✅ ALWAYS use Railway Variables for secrets
```

### Payment Security

✅ HMAC-SHA256 signature verification
✅ Webhook IP whitelisting
✅ PCI DSS compliance (Razorpay handles)
✅ SSL/TLS encryption
✅ No card data in your database

---

## STEP 11: Settlement & Payouts

### To Your UK Bank Account

1. Go to Dashboard → Settlement Accounts
2. Add UK bank details:
   - Account name
   - Account number
   - Sort code
3. Razorpay verifies (1-2 days)
4. Money transfers automatically (Daily/Weekly)

---

## STEP 12: Pricing Models

### Option 1: Direct Pricing (Your Cost)

```
User pays:     ₹499
You keep:      ₹484 (after fees)
Profit margin: Whatever you want

Free plan:     ₹0 (give 25 credits)
Premium:       ₹499 (give 5000 credits)
Diamond:       ₹999 (give unlimited)
```

### Option 2: Subscription Model

```
Premium:       ₹99/month (recurring)
Diamond:       ₹299/month (recurring)

Using Razorpay Subscriptions API
```

---

## STEP 13: Compliance & Taxes

### For UK Business

✅ VAT Registration (if turnover > £85k)
✅ Income tax reporting
✅ Business accounts/invoices
✅ Terms of Service mentioning payments
✅ Privacy policy

### Razorpay Handles

✅ PCI DSS compliance
✅ Fraud detection
✅ Chargeback protection
✅ Payment processing regulation

---

## STEP 14: Monitoring & Analytics

### In Razorpay Dashboard

1. **Payments → Transactions** - See all charges
2. **Analytics** - Revenue, success rate
3. **Customers** - Repeat customers
4. **Disputes** - Handle chargebacks
5. **Reconciliation** - Match with bank

---

## 🎯 COMPLETE PRODUCTION CHECKLIST

- [ ] Create Razorpay business account
- [ ] Complete KYC verification
- [ ] Get Live API keys
- [ ] Set up Razorpay webhook
- [ ] Copy Live Keys to Railway Variables
- [ ] Deploy bot with Live keys
- [ ] Test with small payment (£1-5)
- [ ] Verify: Payment charged
- [ ] Verify: Credits added to user
- [ ] Verify: Bank received payment
- [ ] Announce to users
- [ ] Monitor transactions
- [ ] Handle support issues
- [ ] Check settlements daily

---

## 💰 REAL PAYMENT FLOW (EXAMPLE)

```
User: "/start"
  ↓
Bot: "Welcome! You have 25 free credits"
  ↓
User: "Click [💎 Diamond - ₹999]"
  ↓
Bot: "Creating payment..."
  ↓
Razorpay: "Enter card details"
User: "4532012345678901 | 12/25 | 123"
  ↓
REAL MONEY CHARGED:
  Card: 4532012345678901 (UK Lloyds Bank)
  Amount: £11.75 (≈ ₹999)
  Status: ✅ CAPTURED
  ↓
Razorpay webhook → Your bot:
  "payment.captured"
  payment_id: pay_xxxxx
  ↓
Bot database:
  User credits: 25 → UNLIMITED
  Payment logged: ✅
  ↓
Bot: "✅ Payment successful! ∞ credits added"
  ↓
Razorpay dashboard:
  Transaction logged
  Fee deducted (2.9%)
  ↓
UK Bank Account:
  £11.32 received (after Razorpay fee)
```

---

## ⚠️ IMPORTANT NOTES

1. **USE LIVE KEYS ONLY** - Not test keys
2. **UK USER CARDS WORK** - Will be charged in GBP or INR
3. **MONEY IS REAL** - Check bank account daily
4. **SECURE KEYS** - Never share credentials
5. **HANDLE CHARGEBACKS** - Have good support
6. **MONITOR FRAUD** - Use Razorpay's tools
7. **SETTLEMENTS** - Can take 1-2 days to reach bank

---

## 🚀 YOU'RE READY FOR REAL CHARGES!

1. Set up Razorpay account (₹0 signup, pay only on charges)
2. Get Live keys
3. Add to Railway Variables
4. Deploy
5. **REAL UK CARDS = REAL CHARGES = REAL REVENUE** ✅

