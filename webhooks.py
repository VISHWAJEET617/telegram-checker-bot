#!/usr/bin/env python3
"""
Razorpay Webhook Handler - Production Level
Handles payment confirmations and credit assignments
"""

import logging
import os
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles Razorpay webhooks for real payments"""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook handler"""
        self.webhook_secret = webhook_secret or os.getenv("RAZORPAY_WEBHOOK_SECRET")
        self.enabled = bool(self.webhook_secret)
        
        if self.enabled:
            logger.info("✅ Webhook handler initialized")
        else:
            logger.warning("⚠️ Webhook secret not configured")
    
    def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature using HMAC-SHA256
        
        Args:
            body: Raw webhook body (bytes)
            signature: Signature from X-Razorpay-Signature header
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.enabled:
            logger.warning("Webhook secret not configured - skipping verification")
            return True  # Allow in test mode
        
        try:
            # Generate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = expected_signature == signature
            
            if is_valid:
                logger.info("✅ Webhook signature verified")
            else:
                logger.warning("❌ Webhook signature verification failed")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def handle_payment_captured(self, payload: Dict, db, bot) -> bool:
        """
        Handle payment.captured webhook event
        Adds credits to user when payment is successful
        
        Args:
            payload: Webhook payload with payment details
            db: Database instance
            bot: Telegram bot instance
        
        Returns:
            True if successful, False if failed
        """
        try:
            # Extract payment details
            payment_data = payload.get("payment", {}).get("entity", {})
            payment_id = payment_data.get("id")
            order_id = payment_data.get("order_id")
            amount = payment_data.get("amount")  # in paise
            amount_rupees = amount / 100 if amount else 0
            notes = payment_data.get("notes", {})
            user_id = int(notes.get("user_id", 0))
            plan = notes.get("plan", "unknown")
            
            logger.info(f"Processing payment: {payment_id}, user: {user_id}, plan: {plan}")
            
            if not user_id or user_id == 0:
                logger.error(f"Invalid user_id in webhook: {user_id}")
                return False
            
            # Get plan details
            PLANS = {
                "plan_free": {"credits": 25, "name": "Free"},
                "plan_premium": {"credits": 5000, "name": "Premium"},
                "plan_diamond": {"credits": float('inf'), "name": "Diamond"}
            }
            
            plan_info = PLANS.get(plan, {})
            credits_to_add = plan_info.get("credits", 0)
            plan_name = plan_info.get("name", "Unknown")
            
            if credits_to_add == 0:
                logger.error(f"Unknown plan: {plan}")
                return False
            
            # Add credits to user
            if credits_to_add == float('inf'):
                # Diamond plan - set to unlimited
                db.set_user_plan(user_id, "diamond")
                credit_message = "∞ Unlimited credits"
            else:
                db.update_credits(user_id, int(credits_to_add))
                credit_message = f"{int(credits_to_add):,} credits"
            
            # Log payment in database
            db.log_payment(user_id, order_id, payment_id, amount_rupees, plan, "confirmed")
            
            # Confirm payment status
            db.confirm_payment(payment_id)
            
            # Get updated credits
            current_credits = db.get_user_credits(user_id)
            
            # Notify user in Telegram
            try:
                success_message = (
                    f"✅ <b>Payment Successful!</b>\n\n"
                    f"💳 Amount: ₹{amount_rupees:.2f}\n"
                    f"📦 Plan: <b>{plan_name}</b>\n"
                    f"💎 {credit_message}\n\n"
                    f"🎉 Ready to check cards!\n"
                    f"Send /help for commands"
                )
                
                await bot.send_message(user_id, success_message)
                logger.info(f"User {user_id} notified of payment")
            
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
                # Don't fail - payment was successful even if notification failed
            
            logger.info(f"✅ Payment processed: user={user_id}, amount=₹{amount_rupees:.2f}, credits={credit_message}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling payment.captured: {e}", exc_info=True)
            return False
    
    async def handle_payment_failed(self, payload: Dict, db, bot) -> bool:
        """
        Handle payment.failed webhook event
        Notifies user of failed payment
        
        Args:
            payload: Webhook payload with payment details
            db: Database instance
            bot: Telegram bot instance
        
        Returns:
            True if handled successfully
        """
        try:
            payment_data = payload.get("payment", {}).get("entity", {})
            payment_id = payment_data.get("id")
            notes = payment_data.get("notes", {})
            user_id = int(notes.get("user_id", 0))
            reason = payment_data.get("description", "Unknown reason")
            
            logger.warning(f"Payment failed: {payment_id}, user: {user_id}, reason: {reason}")
            
            if user_id and user_id > 0:
                try:
                    failure_message = (
                        f"❌ <b>Payment Failed</b>\n\n"
                        f"Reason: {reason}\n\n"
                        f"🔄 Please try again or contact support"
                    )
                    await bot.send_message(user_id, failure_message)
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id} of payment failure: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error handling payment.failed: {e}")
            return False
    
    async def handle_payment_authorized(self, payload: Dict, db, bot) -> bool:
        """
        Handle payment.authorized webhook event
        (Before capture - for 3D Secure or manual capture)
        
        Args:
            payload: Webhook payload
            db: Database instance
            bot: Telegram bot instance
        
        Returns:
            True if handled successfully
        """
        try:
            payment_data = payload.get("payment", {}).get("entity", {})
            payment_id = payment_data.get("id")
            notes = payment_data.get("notes", {})
            user_id = int(notes.get("user_id", 0))
            
            logger.info(f"Payment authorized: {payment_id}, user: {user_id}")
            
            if user_id and user_id > 0:
                try:
                    auth_message = (
                        f"⏳ <b>Payment Authorized</b>\n\n"
                        f"Your payment is being processed...\n"
                        f"Credits will be added shortly."
                    )
                    await bot.send_message(user_id, auth_message)
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id} of auth: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error handling payment.authorized: {e}")
            return False
    
    async def process_webhook(self, payload: Dict, db, bot) -> Dict:
        """
        Process any Razorpay webhook event
        
        Args:
            payload: Full webhook payload
            db: Database instance
            bot: Telegram bot instance
        
        Returns:
            Response dict with status
        """
        try:
            event = payload.get("event")
            logger.info(f"Processing webhook event: {event}")
            
            if event == "payment.captured":
                # Real money charged - add credits
                success = await self.handle_payment_captured(payload, db, bot)
            
            elif event == "payment.authorized":
                # Payment authorized but not captured yet
                success = await self.handle_payment_authorized(payload, db, bot)
            
            elif event == "payment.failed":
                # Payment failed - notify user
                success = await self.handle_payment_failed(payload, db, bot)
            
            else:
                logger.warning(f"Unhandled webhook event: {event}")
                success = True  # Don't fail for unknown events
            
            return {
                "status": "success" if success else "error",
                "event": event,
                "processed": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

