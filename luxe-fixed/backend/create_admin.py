"""
Run this ONCE to create/reset the admin user with a fresh password hash.
Usage: python create_admin.py
"""
from flask_bcrypt import Bcrypt
import pymysql

bcrypt = Bcrypt()
pw_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
print(f"Hash: {pw_hash}")

DB = dict(host='localhost', user='root', password='', db='luxe_store',
          charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
conn = pymysql.connect(**DB)
with conn.cursor() as cur:
    cur.execute("SELECT id FROM users WHERE email='admin@luxe.com'")
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE users SET password=%s WHERE email='admin@luxe.com'", (pw_hash,))
        print("Admin password updated.")
    else:
        cur.execute("INSERT INTO users (name, email, password, role) VALUES ('Admin','admin@luxe.com',%s,'admin')", (pw_hash,))
        print("Admin user created.")
    conn.commit()
conn.close()
print("Done! Login: admin@luxe.com / admin123")
