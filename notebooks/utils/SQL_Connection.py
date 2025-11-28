import mysql.connector
from mysql.connector import Error
from datetime import datetime

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        # port=3307,
        user="root",
        password='Shiva2003',
        database='User_Behaviour'
    )
    
def getConnection():
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    return conn, cursor

def getUser(conn, cursor, email):
    query = "select user_id from User where email=%s"
    cursor.execute(query, (email, ))
    result = cursor.fetchone()
    return result[0]
    
