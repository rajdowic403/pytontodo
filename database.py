import mysql.connector
from mysql.connector import Error

def init_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS todo_app")
        cursor.execute("USE todo_app")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category_id INT,
            is_completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )""")
        
        # Domyślne kategorie
        cursor.execute("INSERT IGNORE INTO categories (name) VALUES ('Praca'), ('Dom'), ('Studia')")
        
        conn.commit()
        
    except Error as e:
        print(f"Błąd podczas inicjalizacji bazy danych: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="todo_app"
        )
    except Error as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return None