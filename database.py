#!/usr/bin/env python3
"""Database - User Balances, ₹10 per check"""

import sqlite3
import os
from datetime import datetime
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "data/checker.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance INTEGER DEFAULT 0,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_last4 TEXT,
                status TEXT,
                result TEXT,
                cost INTEGER DEFAULT 1000,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            
            c.execute("""CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id TEXT,
                payment_id TEXT,
                amount REAL,
                type TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            
            conn.commit()
            conn.close()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ DB error: {e}")
    
    def add_user(self, user_id: int, username: str, first_name: str = "User"):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT OR IGNORE INTO users 
                        (user_id, username, first_name, balance) 
                        VALUES (?, ?, ?, 0)""", 
                      (user_id, username, first_name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def get_user_balance(self, user_id: int) -> int:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            return result[0] if result else 0
        except:
            return 0
    
    def add_balance(self, user_id: int, amount: int):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", 
                      (amount, user_id))
            c.execute("""INSERT INTO transactions 
                        (user_id, amount, type, description) 
                        VALUES (?, ?, ?, ?)""",
                      (user_id, amount, "credit", f"Added ₹{amount/100}"))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def deduct_balance(self, user_id: int, amount: int) -> bool:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            
            if not result or result[0] < amount:
                conn.close()
                return False
            
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", 
                      (amount, user_id))
            c.execute("""INSERT INTO transactions 
                        (user_id, amount, type, description) 
                        VALUES (?, ?, ?, ?)""",
                      (user_id, amount, "debit", f"Card check -₹{amount/100}"))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def log_check(self, user_id: int, card_last4: str, status: str, result: str, cost: int = 1000):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT INTO checks 
                        (user_id, card_last4, status, result, cost) 
                        VALUES (?, ?, ?, ?, ?)""",
                      (user_id, card_last4, status, result, cost))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def log_payment(self, user_id: int, order_id: str, payment_id: str, 
                   amount: float, payment_type: str, status: str = "pending"):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""INSERT INTO payments 
                        (user_id, order_id, payment_id, amount, type, status) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                      (user_id, order_id, payment_id, amount, payment_type, status))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def get_user_stats(self, user_id: int) -> dict:
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ?", (user_id,))
            total = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM checks WHERE user_id = ? AND status = 'ALIVE'", 
                      (user_id,))
            alive = c.fetchone()[0]
            
            c.execute("SELECT SUM(cost) FROM checks WHERE user_id = ?", (user_id,))
            spent_paise = c.fetchone()[0] or 0
            
            conn.close()
            return {
                "total": total,
                "alive": alive,
                "spent_rupees": spent_paise / 100
            }
        except:
            return {"total": 0, "alive": 0, "spent_rupees": 0}

