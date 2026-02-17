import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS usernames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'unknown',
                    last_check TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified INTEGER DEFAULT 0
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES 
                ('monitoring_active', '0'),
                ('check_interval', '1'),
                ('batch_size', '50'),
                ('spam_delay', '0.5'),
                ('spam_mode', 'count'),
                ('spam_message_count', '10'),
                ('spam_chat_id', '')
            ''')
            
            await db.commit()
    
    async def add_username(self, username: str) -> bool:
        username = username.lstrip('@').lower()
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        'INSERT INTO usernames (username, status) VALUES (?, ?)',
                        (username, 'unknown')
                    )
                    await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False
    
    async def add_usernames_bulk(self, usernames: List[str]) -> Dict[str, int]:
        added = 0
        skipped = 0
        
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                for username in usernames:
                    username = username.lstrip('@').lower().strip()
                    if not username:
                        continue
                    try:
                        await db.execute(
                            'INSERT INTO usernames (username, status) VALUES (?, ?)',
                            (username, 'unknown')
                        )
                        added += 1
                    except aiosqlite.IntegrityError:
                        skipped += 1
                await db.commit()
        
        return {'added': added, 'skipped': skipped}
    
    async def remove_username(self, username: str) -> bool:
        username = username.lstrip('@').lower()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'DELETE FROM usernames WHERE username = ?',
                    (username,)
                )
                await db.commit()
                return cursor.rowcount > 0
    
    async def get_all_usernames(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM usernames ORDER BY created_at DESC'
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_usernames_for_check(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT username FROM usernames')
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_free_usernames(self) -> List[str]:
        """Получает список username со статусом 'free'"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT username FROM usernames WHERE status = 'free'"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def update_username_status(self, username: str, status: str):
        username = username.lstrip('@').lower()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'SELECT status FROM usernames WHERE username = ?',
                    (username,)
                )
                row = await cursor.fetchone()
                old_status = row[0] if row else None
                
                await db.execute(
                    'UPDATE usernames SET status = ?, last_check = ? WHERE username = ?',
                    (status, datetime.now(), username)
                )
                
                if old_status and old_status != status:
                    await db.execute(
                        'INSERT INTO logs (username, old_status, new_status) VALUES (?, ?, ?)',
                        (username, old_status, status)
                    )
                
                await db.commit()
                return old_status
    
    async def mark_as_notified(self, username: str):
        username = username.lstrip('@').lower()
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'UPDATE usernames SET notified = 1 WHERE username = ?',
                    (username,)
                )
                await db.commit()
    
    async def get_statistics(self) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM usernames')
            total = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM usernames WHERE status = 'occupied'"
            )
            occupied = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM usernames WHERE status = 'free'"
            )
            free = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM usernames WHERE status = 'error'"
            )
            error = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM usernames WHERE status = 'unknown'"
            )
            unknown = (await cursor.fetchone())[0]
            
            return {
                'total': total,
                'occupied': occupied,
                'free': free,
                'error': error,
                'unknown': unknown
            }
    
    async def get_setting(self, key: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT value FROM settings WHERE key = ?',
                (key,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def set_setting(self, key: str, value: str):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                    (key, value)
                )
                await db.commit()
    
    async def clear_all_usernames(self):
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM usernames')
                await db.commit()
    
    async def export_usernames(self) -> str:
        usernames = await self.get_all_usernames()
        lines = []
        for u in usernames:
            lines.append(f"@{u['username']},{u['status']},{u['last_check'] or 'never'}")
        return '\n'.join(lines)
