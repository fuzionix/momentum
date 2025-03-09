import os
import time
import pymysql

def initialize_database():
    """Initialize database"""
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', ''),
                password=os.getenv('DB_PASSWORD', ''),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute("CREATE DATABASE IF NOT EXISTS momentum")
                cursor.execute("USE momentum")
                
                cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    credits INT DEFAULT 3,
    language VARCHAR(10) DEFAULT 'en',
    last_reset DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (telegram_id)
)
                """)
                
                cursor.execute("""
CREATE TABLE IF NOT EXISTS analysis_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ticker_symbol VARCHAR(20) NOT NULL,
    replicate_id VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
                """)
                
                connection.commit()
                print("Database initialized successfully")
                return True
                
        except pymysql.MySQLError as e:
            attempt += 1
            wait_time = 5 * attempt  # Exponential backoff
            print(f"Database initialization attempt {attempt} failed: {e}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()
    
    print("Failed to initialize database after multiple attempts")
    return False

if __name__ == "__main__":
    initialize_database()