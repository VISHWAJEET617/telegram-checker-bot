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
            logger.warning("⚠️ Razorpay credentials not configured")
    
    def create_order(self, user_id: int, amount: int, plan: str) -> Dict:
        """Create payment order"""
        if not self.enabled:
            return {"status": "error", "message": "Razorpay not configured"}
        
        try:
            # In real implementation, call Razorpay API
            # For now, return mock response
            
            order_data = {
                "user_id": user_id,
                "amount": amount,
                "plan": plan,
                "status": "pending"
            }
            
            logger.info(f"Order created for user {user_id}: {amount} INR for {plan} plan")
            return {"status": "success", "order_id": "order_123", "data": order_data}
        
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {"status": "error", "message": str(e)}
    
    def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify payment signature"""
        if not self.enabled:
            return False
        
        try:
            # In real implementation, verify with Razorpay API
            # Using HMAC-SHA256
            
            import hmac
            import hashlib
            
            message = f"{order_id}|{payment_id}"
            expected_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = expected_signature == signature
            
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
            "free": {
                "amount": 0,
                "credits": 25,
                "duration": "Forever"
            },
            "premium": {
                "amount": 499,
                "credits": 5000,
                "duration": "30 days"
            },
            "diamond": {
                "amount": 999,
                "credits": float('inf'),
                "duration": "30 days"
            }
        }
    
    def is_enabled(self) -> bool:
        """Check if gateway is enabled"""
        return self.enabled

