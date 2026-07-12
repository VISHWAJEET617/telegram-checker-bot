#!/usr/bin/env python3
"""
Database Module - SQLite Database Management
Handles all user data and transactions
"""

import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "data/checker.db"):
        """Initialize database"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            credits INTEGER DEFAULT 25,
            plan TEXT DEFAULT 'free',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME
        )""")
        
        # Transactions table
        c.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )""")
        
        # Checks table
        c.execute("""CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_last4 TEXT,
            status TEXT,
            result TEXT,
            cost INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )""")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def add_user(self, user_id: int, username: str, first_name: str = "Unknown"):
        """Add new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""INSERT OR IGNORE INTO users 
                        (user_id, username, first_name) 
                        VALUES (?, ?, ?)""", 
                      (user_id, username, first_name))
            conn.commit()
            conn.close()
            logger.info(f"✅ User {user_id} added")
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")
    
    def get_user_credits(self, user_id: int) -> int:
        """Get user credits"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Error getting credits: {e}")
            return 0
    
    def get_user_plan(self, user_id: int) -> str:
        """Get user plan"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            return result[0] if result else "free"
        except Exception as e:
            logger.error(f"❌ Error getting plan: {e}")
            return "free"
    
    def update_credits(self, user_id: int, amount: int):
        """Update user credits"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", 
                      (amount, user_id))
            
            # Log transaction
            c.execute("""INSERT INTO transactions 
                        (user_id, amount, type, description) 
                        VALUES (?, ?, ?, ?)""",
                      (user_id, amount, "credit" if amount > 0 else "debit", 
                       f"Credits {'added' if amount > 0 else 'used'}"))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Credits updated for user {user_id}: {amount}")
        except Exception as e:
            logger.error(f"❌ Error updating credits: {e}")
    
    def set_user_plan(self, user_id: int, plan: str):
        """Set user plan"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE users SET plan = ? WHERE user_id = ?", 
                      (plan, user_id))
            conn.commit()
            conn.close()
            logger.info(f"✅ Plan updated for user {user_id}: {plan}")
        except Exception as e:
            logger.error(f"❌ Error setting plan: {e}")
    
    def log_check(self, user_id: int, card_last4: str, status: str, result: str, cost: int = 1):
        """Log a card check"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""INSERT INTO checks 
                        (user_id, card_last4, status, result, cost) 
                        VALUES (?, ?, ?, ?, ?)""",
                      (user_id, card_last4, status, result, cost))
            conn.commit()
            conn.close()
            logger.info(f"✅ Check logged for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error logging check: {e}")
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ?", (user_id,))
            total_checks = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ? AND status = 'ALIVE'", 
                      (user_id,))
            alive_checks = c.fetchone()[0]
            
            c.execute("SELECT SUM(cost) FROM checks WHERE user_id = ?", (user_id,))
            total_spent = c.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_checks": total_checks,
                "alive_checks": alive_checks,
                "total_spent": total_spent
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {"total_checks": 0, "alive_checks": 0, "total_spent": 0}
    
    def get_all_users_count(self) -> int:
        """Get total users count"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            count = c.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"❌ Error getting users count: {e}")
            return 0

