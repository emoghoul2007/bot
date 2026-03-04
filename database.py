import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                language TEXT DEFAULT 'en',
                joined_date TEXT,
                orders_count INTEGER DEFAULT 0
            )
        ''')
        
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_type TEXT,
                photos_count INTEGER,
                status TEXT DEFAULT 'pending',
                crypto_invoice_id TEXT,
                stars_invoice_payload TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_user_language(self, user_id: int) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'en'

    def set_user_language(self, user_id: int, language: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, language, joined_date)
            VALUES (?, ?, ?)
        ''', (user_id, language, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def add_order(self, user_id: int, product_type: str, photos_count: int, crypto_invoice_id: Optional[str] = None, stars_invoice_payload: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (user_id, product_type, photos_count, crypto_invoice_id, stars_invoice_payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, product_type, photos_count, crypto_invoice_id, stars_invoice_payload, datetime.now().isoformat()))
        
        order_id = cursor.lastrowid
        
        # Update user's orders count
        cursor.execute('UPDATE users SET orders_count = orders_count + 1 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return order_id

    def update_order_status(self, order_id: int, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        
        conn.commit()
        conn.close()

    def get_pending_crypto_orders(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, crypto_invoice_id, status FROM orders 
            WHERE user_id = ? AND crypto_invoice_id IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_order_by_stars_payload(self, payload: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, product_type FROM orders 
            WHERE stars_invoice_payload = ?
        ''', (payload,))
        result = cursor.fetchone()
        conn.close()
        return result