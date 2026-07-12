#!/usr/bin/env python3
"""
Database Module - SQLite Database Management
Handles all user data and transactions with connection pooling
"""

import sqlite3
import os
from datetime import datetime
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "data/checker.db", pool_size: int = 5):
        """Initialize database with connection pool"""
        self.db_path = db_path
        self.pool_size = pool_size
        self.connection_pool = []
        self.pool_lock = Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        """Get connection from pool or create new one"""
        with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def return_connection(self, conn):
        """Return connection to pool"""
        with self.pool_lock:
            if len(self.connection_pool) < self.pool_size:
                self.connection_pool.append(conn)
            else:
                conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Users table
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
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
            
            # Payments table
            c.execute("""CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT UNIQUE,
                payment_id TEXT UNIQUE,
                amount REAL,
                plan TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )""")
            
            conn.commit()
            self.return_connection(conn)
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    def add_user(self, user_id: int, username: str, first_name: str = "Unknown"):
        """Add new user (insert or update)"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT OR REPLACE INTO users 
                        (user_id, username, first_name, last_active) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)""", 
                      (user_id, username, first_name))
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ User {user_id} registered/updated")
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")
    
    def get_user_credits(self, user_id: int) -> int:
        """Get user credits"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            self.return_connection(conn)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Error getting credits: {e}")
            return 0
    
    def get_user_plan(self, user_id: int) -> str:
        """Get user plan"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            self.return_connection(conn)
            return result[0] if result else "free"
        except Exception as e:
            logger.error(f"❌ Error getting plan: {e}")
            return "free"
    
    def update_credits(self, user_id: int, amount: int):
        """Update user credits and log transaction"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Verify user exists
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            if not c.fetchone():
                logger.warning(f"User {user_id} not found")
                self.return_connection(conn)
                return
            
            # Update credits
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", 
                      (amount, user_id))
            
            # Log transaction
            c.execute("""INSERT INTO transactions 
                        (user_id, amount, type, description) 
                        VALUES (?, ?, ?, ?)""",
                      (user_id, amount, "credit" if amount > 0 else "debit", 
                       f"Credits {'added' if amount > 0 else 'used'}"))
            
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Credits updated for user {user_id}: {amount:+d}")
        except Exception as e:
            logger.error(f"❌ Error updating credits: {e}")
    
    def set_user_plan(self, user_id: int, plan: str):
        """Set user plan"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("UPDATE users SET plan = ? WHERE user_id = ?", 
                      (plan, user_id))
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Plan updated for user {user_id}: {plan}")
        except Exception as e:
            logger.error(f"❌ Error setting plan: {e}")
    
    def log_check(self, user_id: int, card_last4: str, status: str, result: str, cost: int = 1):
        """Log a card check"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT INTO checks 
                        (user_id, card_last4, status, result, cost) 
                        VALUES (?, ?, ?, ?, ?)""",
                      (user_id, card_last4, status, result, cost))
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Check logged for user {user_id}: {status}")
        except Exception as e:
            logger.error(f"❌ Error logging check: {e}")
    
    def log_payment(self, user_id: int, order_id: str, payment_id: str, 
                   amount: float, plan: str, status: str = "pending"):
        """Log a payment attempt"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT INTO payments 
                        (user_id, order_id, payment_id, amount, plan, status) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                      (user_id, order_id, payment_id, amount, plan, status))
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Payment logged: {order_id}")
        except Exception as e:
            logger.error(f"❌ Error logging payment: {e}")
    
    def confirm_payment(self, payment_id: str):
        """Mark payment as confirmed"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("UPDATE payments SET status = 'confirmed' WHERE payment_id = ?", 
                      (payment_id,))
            conn.commit()
            self.return_connection(conn)
            logger.info(f"✅ Payment confirmed: {payment_id}")
        except Exception as e:
            logger.error(f"❌ Error confirming payment: {e}")
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ?", (user_id,))
            total_checks = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ? AND status = 'ALIVE'", 
                      (user_id,))
            alive_checks = c.fetchone()[0]
            
            c.execute("SELECT SUM(cost) FROM checks WHERE user_id = ?", (user_id,))
            total_spent = c.fetchone()[0] or 0
            
            self.return_connection(conn)
            
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
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            count = c.fetchone()[0]
            self.return_connection(conn)
            return count
        except Exception as e:
            logger.error(f"❌ Error getting users count: {e}")
            return 0

    
    def get_payment_plan(self, order_id: str) -> str:
        """Get plan from payment order"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT plan FROM payments WHERE order_id = ?", (order_id,))
            result = c.fetchone()
            self.return_connection(conn)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Error getting payment plan: {e}")
            return None
