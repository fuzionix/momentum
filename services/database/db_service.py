import os
import pymysql
from datetime import datetime, timedelta

class DatabaseService:
    def __init__(self):
        self.connection = None
        self.connect()
        
    def connect(self):
        '''Establish connection to the MySQL database'''
        try:
            self.connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', ''),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'momentum'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print('Database connection established successfully')
        except Exception as e:
            print(f'Error connecting to database: {e}')

    def ensure_connection(self):
        '''Ensure database connection is alive, reconnect if needed'''
        try:
            if self.connection is None or not self.connection.open:
                self.connect()
            self.connection.ping(reconnect=True)
        except Exception as e:
            print(f'Connection lost, reconnecting: {e}')
            self.connect()
    
    def get_user(self, telegram_id):
        '''Get user by Telegram ID'''
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            sql = 'SELECT * FROM users WHERE telegram_id = %s'
            cursor.execute(sql, (telegram_id,))
            return cursor.fetchone()
    
    def create_user(self, telegram_id, username=None, first_name=None, last_name=None, language=None):
        '''Create a new user in the database'''
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            sql = '''
INSERT INTO users (telegram_id, username, first_name, last_name, language) 
VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (telegram_id, username, first_name, last_name, language))
            self.connection.commit()
            return self.get_user(telegram_id)
    
    def update_user(self, telegram_id, username=None, first_name=None, last_name=None, language=None):
        '''Update user information'''
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            # Build dynamic update query based on provided fields
            updates = []
            params = []
            
            if username is not None:
                updates.append('username = %s')
                params.append(username)
            
            if first_name is not None:
                updates.append('first_name = %s')
                params.append(first_name)
                
            if last_name is not None:
                updates.append('last_name = %s')
                params.append(last_name)

            if language is not None:
                updates.append('language = %s')
                params.append(language)
            
            if not updates:
                # Nothing to update
                return self.get_user(telegram_id)
                
            update_clause = ', '.join(updates)
            params.append(telegram_id)
            
            sql = f'UPDATE users SET {update_clause} WHERE telegram_id = %s'
            cursor.execute(sql, params)
            self.connection.commit()
            return self.get_user(telegram_id)
    
    def get_or_create_user(self, telegram_id, username=None, first_name=None, last_name=None, language=None):
        '''Get user or create if not exists'''
        user = self.get_user(telegram_id)
        if user:
            # Update user information if it's changed
            return self.update_user(telegram_id, username, first_name, last_name, language)
        else:
            return self.create_user(telegram_id, username, first_name, last_name, language)
    
    def log_analysis(self, user_id, ticker_symbol, replicate_id):
        '''Log an analysis request'''
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            sql = '''
INSERT INTO analysis_logs (user_id, ticker_symbol, replicate_id)
VALUES (%s, %s, %s)
            '''
            cursor.execute(sql, (user_id, ticker_symbol, replicate_id))
            self.connection.commit()
            return cursor.lastrowid
        
    def get_user_credits(self, telegram_id):
        '''Get user's current credits and check if they need renewal'''
        user = self.get_user(telegram_id)
        if not user:
            return 0
        
        self.check_and_renew_credits(user)
        
        updated_user = self.get_user(telegram_id)
        return updated_user['credits']
    
    def check_and_renew_credits(self, user):
        '''Check if credits need to be renewed and update them'''
        self.ensure_connection()
        
        last_reset = user['last_reset']
        current_time = datetime.now()
        
        # If last reset was more than 24 hours ago, renew credits
        if (current_time - last_reset).days >= 1:
            with self.connection.cursor() as cursor:
                if user['credits'] < 3:
                    sql = '''
UPDATE users 
SET credits = 3, last_reset = %s 
WHERE id = %s
                    '''
                    cursor.execute(sql, (current_time, user['id']))
                else:
                    sql = '''
UPDATE users 
SET last_reset = %s 
WHERE id = %s
                    '''
                    cursor.execute(sql, (current_time, user['id']))
                
                self.connection.commit()
    
    def use_credit(self, telegram_id):
        '''Use one credit for analysis. Returns (success, credits_left)'''
        user = self.get_user(telegram_id)
        if not user:
            return False, 0
            
        self.check_and_renew_credits(user)
        user = self.get_user(telegram_id)
        
        if user['credits'] <= 0:
            return False, 0
            
        # Use one credit
        self.ensure_connection()
        with self.connection.cursor() as cursor:
            sql = '''
UPDATE users
SET credits = credits - 1
WHERE telegram_id = %s
            '''
            cursor.execute(sql, (telegram_id,))
            self.connection.commit()
            
        updated_user = self.get_user(telegram_id)
        return True, updated_user['credits']
    
    def get_credits_info(self, telegram_id):
        '''Get detailed information about user's credits'''
        user = self.get_user(telegram_id)
        if not user:
            return {
                'credits': 0,
                'last_reset': datetime.now(),
                'next_reset': datetime.now() + timedelta(days=1)
            }
            
        self.check_and_renew_credits(user)
        user = self.get_user(telegram_id)
        next_reset = user['last_reset'] + timedelta(days=1)
        
        return {
            'credits': user['credits'],
            'last_reset': user['last_reset'],
            'next_reset': next_reset
        }
            
    def close(self):
        '''Close the database connection'''
        if self.connection and self.connection.open:
            self.connection.close()