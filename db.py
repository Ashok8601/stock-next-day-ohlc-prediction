import sqlite3
database="user.db"
def get_db():
    conn=sqlite3.connect(database)
    conn.row_factory=sqlite3.Row
    return conn
def create_table():
    conn=get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS user(
        id INTEGER PRIMARY KEY AUTOINCREMENT ,
        name TEXT ,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL )""")
    conn.commit()
    conn.close()
    print("user tabel created successfully")
create_table()    