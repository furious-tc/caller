import sqlite3

try:
    conn = sqlite3.connect('db.sqlite3')
    print('[INFO] База данных создана!')
except:
    print('[INFO] Ошибка подключения')

cursor = conn.cursor()

cursor.execute(f'''
CREATE TABLE users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	telegram_id integer NOT NULL UNIQUE,
	username text
);''')

cursor.execute(f'''
CREATE TABLE sms (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	request_number text NOT NULL UNIQUE,
	user_id integer NOT NULL,
	phone text NOT NULL UNIQUE,
	admin_id integer,
    answer_sms text,
    FOREIGN KEY (user_id)
        REFERENCES users (telegram_id)
);''')

cursor.execute(f'''
CREATE TABLE admins (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	admin_id integer NOT NULL
);''')

