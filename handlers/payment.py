#!/usr/bin/env python3
"""
Payment Handler - Payment Processing Integration
Razorpay and other payment gateway callbacks
"""

import logging
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from gates.razorpay import RazorpayGate
from keyboards import home_keyboard, back_button

logger = logging.getLogger(__name__)

# Initialize Razorpay gate
razorpay = RazorpayGate(
    key_id=os.getenv("RAZORPAY_KEY_ID"),
    key_secret=os.getenv("RAZORPAY_KEY_SECRET")
)

# Plan pricing
PLANS = {
    "plan_free": {
        "name": "Free",
        "credits": 25,
        "amount": 0,
        "description": "25 credits - Free forever"
    },
    "plan_premium": {
        "name": "Premium",
        "credits": 5000,
        "amount": 49900,  # 499 INR in paise
        "description": "5000 credits - One time"
    },
    "plan_diamond": {
        "name": "Diamond",
        "credits": float('inf'),
        "amount": 99900,  # 999 INR in paise
        "description": "Unlimited credits - One time"
    }
}

async def payment_callback(callback: types.CallbackQuery, db, state: FSMContext):
    """Handle plan selection"""
    plan_key = callback.data
    
    if plan_key not in PLANS:
        await callback.answer("Invalid plan", show_alert=True)
        return
    
    plan = PLANS[plan_key]
    user_id = callback.from_user.id
    
    if plan["amount"] == 0:
        # Free plan - give credits directly
        db.set_user_plan(user_id, "free")
        db.update_credits(user_id, plan["credits"])
        
        await callback.message.edit_text(
            f"🎁 <b>Free Plan Activated</b>\n\n"
            f"Plan: {plan['name']}\n"
            f"Credits: +{plan['credits']}\n"
            f"Status: ✅ Active",
            reply_markup=back_button()
        )
        await callback.answer("Free plan activated!")
    else:
        # Paid plan - create payment order
        await create_payment_order(callback, user_id, db, plan_key, plan)

async def create_payment_order(callback: types.CallbackQuery, user_id: int, db, plan_key: str, plan: dict):
    """Create payment order via Razorpay"""
    if not razorpay.is_enabled():
        await callback.answer(
            "⚠️ Payment gateway not configured. Contact admin.",
            show_alert=True
        )
        return
    
    try:
        # Create order
        order_response = razorpay.create_order(user_id, plan["amount"], plan_key)
        
        if order_response["status"] != "success":
            raise Exception(order_response.get("message", "Failed to create order"))
        
        order_id = order_response.get("order_id")
        
        # Log payment in database
        db.log_payment(user_id, order_id, "", plan["amount"] / 100, plan_key, "pending")
        
        # Show payment link (in production, use Razorpay payment page)
        payment_text = (
            f"💳 <b>Payment Details</b>\n\n"
            f"Plan: {plan['name']}\n"
            f"Amount: ₹{plan['amount'] / 100:.0f}\n"
            f"Credits: {int(plan['credits']) if plan['credits'] != float('inf') else 'Unlimited'}\n\n"
            f"Order ID: <code>{order_id}</code>\n\n"
            f"⏳ <b>Waiting for payment confirmation...</b>\n\n"
            f"In production, redirect to Razorpay payment page.\n"
            f"For testing, use test cards from docs."
        )
        
        await callback.message.edit_text(payment_text, reply_markup=back_button())
        await callback.answer("Order created. Proceed to payment.")
        
        logger.info(f"Payment order created: {order_id} for user {user_id}")
    
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        await callback.answer(f"❌ Payment error: {str(e)}", show_alert=True)

async def razorpay_callback(callback: types.CallbackQuery, db, state: FSMContext):
    """Handle Razorpay gateway selection"""
    user_id = callback.from_user.id
    
    plans_text = (
        "<b>💳 Razorpay Payment Plans</b>\n\n"
        "<b>🎁 Free Plan</b>\n"
        "Credits: 25\n"
        "Price: ₹0 (Free)\n\n"
        "<b>⭐ Premium Plan</b>\n"
        "Credits: 5000\n"
        "Price: ₹499\n\n"
        "<b>💎 Diamond Plan</b>\n"
        "Credits: Unlimited\n"
        "Price: ₹999\n\n"
        "Select a plan using buttons below"
    )
    
    from keyboards import get_payment_plans_keyboard
    
    await callback.message.edit_text(
        plans_text,
        reply_markup=get_payment_plans_keyboard()
    )
    await callback.answer()

async def verify_payment(payment_id: str, order_id: str, signature: str, db, user_id: int):
    """Verify payment signature and confirm"""
    try:
        if razorpay.verify_payment(order_id, payment_id, signature):
            # Payment verified - add credits
            plan_key = db.get_payment_plan(order_id)
            
            if plan_key in PLANS:
                plan = PLANS[plan_key]
                db.set_user_plan(user_id, plan_key.replace("plan_", ""))
                
                if plan["credits"] != float('inf'):
                    db.update_credits(user_id, int(plan["credits"]))
                
                # Mark payment as confirmed
                db.confirm_payment(payment_id)
                
                logger.info(f"Payment verified for user {user_id}: {payment_id}")
                return True
        
        logger.warning(f"Payment verification failed: {payment_id}")
        return False
    
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return False

