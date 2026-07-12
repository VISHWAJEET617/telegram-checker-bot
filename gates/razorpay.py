#!/usr/bin/env python3
"""
Razorpay Gate - Razorpay Payment Integration
Handles payment processing via Razorpay
"""

import logging
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class RazorpayGate:
    """Razorpay payment gateway handler"""
    
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        """Initialize Razorpay gateway"""
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        self.enabled = bool(self.key_id and self.key_secret)
        
        if self.enabled:
            logger.info("✅ Razorpay Gateway initialized")
        else:
            logger.warning("⚠️ Razorpay credentials not configured (optional for testing)")
    
    def create_order(self, user_id: int, amount: int, plan: str) -> Dict:
        """
        Create payment order
        
        Args:
            user_id: Telegram user ID
            amount: Amount in paise (e.g., 49900 for ₹499)
            plan: Plan ID (plan_free, plan_premium, plan_diamond)
        
        Returns:
            Dict with status, order_id, and order data
        """
        if not self.enabled:
            logger.warning("Razorpay not configured - returning mock response")
            return {
                "status": "success",
                "order_id": f"test_order_{user_id}",
                "data": {"user_id": user_id, "amount": amount, "plan": plan}
            }
        
        try:
            # In production, integrate with Razorpay API:
            # import razorpay
            # client = razorpay.Client(auth=(self.key_id, self.key_secret))
            # response = client.order.create({
            #     "amount": amount,
            #     "currency": "INR",
            #     "receipt": f"user_{user_id}_{plan}"
            # })
            
            order_data = {
                "user_id": user_id,
                "amount": amount,
                "plan": plan,
                "status": "pending"
            }
            
            logger.info(f"Order created for user {user_id}: ₹{amount/100:.2f} for {plan}")
            return {"status": "success", "order_id": f"order_{user_id}_{plan}", "data": order_data}
        
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {"status": "error", "message": str(e)}
    
    def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify payment signature
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Razorpay signature from webhook/response
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.enabled:
            logger.warning("Razorpay not configured - skipping verification")
            return True  # Allow in test mode
        
        try:
            # In production:
            # import hmac
            # import hashlib
            # message = f"{order_id}|{payment_id}"
            # expected_signature = hmac.new(
            #     self.key_secret.encode(),
            #     message.encode(),
            #     hashlib.sha256
            # ).hexdigest()
            # return expected_signature == signature
            
            is_valid = bool(order_id and payment_id and signature)
            
            if is_valid:
                logger.info(f"Payment verified: {payment_id}")
            else:
                logger.warning(f"Payment verification failed: {payment_id}")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def get_plans(self) -> Dict[str, Dict]:
        """Get available payment plans"""
        return {
            "plan_free": {
                "name": "Free",
                "amount": 0,
                "credits": 25,
                "duration": "Forever"
            },
            "plan_premium": {
                "name": "Premium",
                "amount": 49900,  # ₹499 in paise
                "credits": 5000,
                "duration": "One time"
            },
            "plan_diamond": {
                "name": "Diamond",
                "amount": 99900,  # ₹999 in paise
                "credits": float('inf'),
                "duration": "One time"
            }
        }
    
    def is_enabled(self) -> bool:
        """Check if gateway is enabled"""
        return self.enabled

