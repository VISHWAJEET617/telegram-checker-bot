#!/usr/bin/env python3
"""Database module for user balance & transaction logging"""

import json
import os
from typing import Dict
from datetime import datetime

class Database:
    """Simple in-memory database with JSON persistence"""
    
    def __init__(self):
        self.data_file = "data.json"
        self.users = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load user data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Save user data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def get_user_balance(self, user_id: int) -> int:
        """Get user balance in paise (₹1 = 100 paise)"""
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "balance": 200000,  # ₹2000 default
                "transactions": []
            }
            self._save_data()
        return self.users[user_id]["balance"]
    
    def deduct_balance(self, user_id: int, amount: int) -> bool:
        """Deduct amount from user balance"""
        user_id = str(user_id)
        balance = self.get_user_balance(user_id)
        
        if balance >= amount:
            self.users[user_id]["balance"] -= amount
            self._save_data()
            return True
        return False
    
    def add_balance(self, user_id: int, amount: int):
        """Add amount to user balance"""
        user_id = str(user_id)
        self.get_user_balance(user_id)  # Ensure user exists
        self.users[user_id]["balance"] += amount
        self._save_data()
    
    def log_check(self, user_id: int, card_last4: str, status: str, response: str, charge: int):
        """Log card check transaction"""
        user_id = str(user_id)
        self.get_user_balance(user_id)  # Ensure user exists
        
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "card": card_last4,
            "status": status,
            "response": response,
            "charge": charge,
            "balance": self.users[user_id]["balance"]
        }
        
        self.users[user_id]["transactions"].append(transaction)
        self._save_data()
    
    def get_transactions(self, user_id: int, limit: int = 10) -> list:
        """Get user transactions"""
        user_id = str(user_id)
        if user_id not in self.users:
            return []
        
        transactions = self.users[user_id]["transactions"]
        return transactions[-limit:]

