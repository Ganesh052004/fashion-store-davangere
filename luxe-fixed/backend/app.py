from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import pymysql
import jwt
import datetime
import os
from flask import send_from_directory


app = Flask(__name__)
CORS(app, origins="*")
bcrypt = Bcrypt(app)


app.config['SECRET_KEY'] = 'luxe_secret_key_2026'

# ── DB CONFIG (XAMPP defaults) ──────────────────────────────────────────────
DB = dict(host='localhost', user='root', password='', db='luxe_store',
          charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

def get_db():
    return pymysql.connect(**DB)

def decode_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return None

def auth_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        data = decode_token(token)
        if not data:
            return jsonify({'error': 'Unauthorized'}), 401
        request.user = data
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        data = decode_token(token)
        if not data or data.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        request.user = data
        return f(*args, **kwargs)
    return decorated

# ── AUTH ─────────────────────────────────────────────────────────────────────
FRONTEND_FOLDER = '../frontend'
@app.route('/')
def home():
    return send_from_directory(FRONTEND_FOLDER, 'login.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_FOLDER, path)

def register():
    d = request.json
    name, email, password = d.get('name'), d.get('email'), d.get('password')
    if not all([name, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                        (name, email, hashed))
            conn.commit()
            user_id = cur.lastrowid
        conn.close()
        token = jwt.encode({'id': user_id, 'email': email, 'role': 'user',
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)},
                           app.config['SECRET_KEY'])
        return jsonify({'token': token, 'role': 'user', 'name': name})
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    email, password = d.get('email'), d.get('password')
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
    conn.close()
    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = jwt.encode({'id': user['id'], 'email': email, 'role': user['role'],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)},
                       app.config['SECRET_KEY'])
    return jsonify({'token': token, 'role': user['role'], 'name': user['name']})

# ── PRODUCTS ─────────────────────────────────────────────────────────────────

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products ORDER BY id")
        products = cur.fetchall()
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@admin_required
def add_product():
    d = request.json
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO products (name, category, price, old_price, emoji, badge, stock)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (d['name'], d['category'], d['price'], d.get('old_price'),
                     d.get('emoji', '👕'), d.get('badge', ''), d.get('stock', 100)))
        conn.commit()
        pid = cur.lastrowid
    conn.close()
    return jsonify({'id': pid, 'message': 'Product added'})

@app.route('/api/products/<int:pid>', methods=['PUT'])
@admin_required
def update_product(pid):
    d = request.json
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""UPDATE products SET name=%s, category=%s, price=%s, old_price=%s,
                       emoji=%s, badge=%s, stock=%s WHERE id=%s""",
                    (d['name'], d['category'], d['price'], d.get('old_price'),
                     d.get('emoji', '👕'), d.get('badge', ''), d.get('stock', 100), pid))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated'})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
@admin_required
def delete_product(pid):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id=%s", (pid,))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted'})

# ── CART ─────────────────────────────────────────────────────────────────────

@app.route('/api/cart', methods=['GET'])
@auth_required
def get_cart():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""SELECT c.id, c.quantity, p.id as product_id,
                       p.name, p.price, p.emoji, p.category
                       FROM cart c JOIN products p ON c.product_id=p.id
                       WHERE c.user_id=%s""", (request.user['id'],))
        items = cur.fetchall()
    conn.close()
    return jsonify(items)

@app.route('/api/cart', methods=['POST'])
@auth_required
def add_to_cart():
    d = request.json
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO cart (user_id, product_id, quantity)
                       VALUES (%s, %s, 1)
                       ON DUPLICATE KEY UPDATE quantity = quantity + 1""",
                    (request.user['id'], d['product_id']))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Added to cart'})

@app.route('/api/cart/<int:product_id>', methods=['DELETE'])
@auth_required
def remove_from_cart(product_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM cart WHERE user_id=%s AND product_id=%s",
                    (request.user['id'], product_id))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Removed from cart'})

@app.route('/api/cart/checkout', methods=['POST'])
@auth_required
def checkout():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""SELECT c.quantity, p.price FROM cart c
                       JOIN products p ON c.product_id=p.id WHERE c.user_id=%s""",
                    (request.user['id'],))
        items = cur.fetchall()
        if not items:
            return jsonify({'error': 'Cart is empty'}), 400
        total = sum(i['price'] * i['quantity'] for i in items)
        cur.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s)",
                    (request.user['id'], total))
        order_id = cur.lastrowid
        cur.execute("""INSERT INTO order_items (order_id, product_id, quantity, price)
                       SELECT %s, c.product_id, c.quantity, p.price
                       FROM cart c JOIN products p ON c.product_id=p.id
                       WHERE c.user_id=%s""", (order_id, request.user['id']))
        cur.execute("DELETE FROM cart WHERE user_id=%s", (request.user['id'],))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Order placed!', 'order_id': order_id, 'total': float(total)})

# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM users WHERE role='user'")
        users = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM orders")
        orders = cur.fetchone()['total']
        cur.execute("SELECT COALESCE(SUM(total),0) as revenue FROM orders WHERE status!='cancelled'")
        revenue = cur.fetchone()['revenue']
        cur.execute("SELECT COUNT(*) as total FROM products")
        products = cur.fetchone()['total']
    conn.close()
    return jsonify({'users': users, 'orders': orders, 'revenue': float(revenue), 'products': products})

@app.route('/api/admin/orders', methods=['GET'])
@admin_required
def admin_orders():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""SELECT o.id, o.total, o.status, o.created_at,
                       u.name as user_name, u.email
                       FROM orders o JOIN users u ON o.user_id=u.id
                       ORDER BY o.created_at DESC""")
        orders = cur.fetchall()
    conn.close()
    for o in orders:
        if hasattr(o['created_at'], 'isoformat'):
            o['created_at'] = o['created_at'].isoformat()
    return jsonify(orders)

@app.route('/api/admin/orders/<int:oid>', methods=['PUT'])
@admin_required
def update_order_status(oid):
    status = request.json.get('status')
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, oid))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Status updated'})

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
        users = cur.fetchall()
    conn.close()
    for u in users:
        if hasattr(u['created_at'], 'isoformat'):
            u['created_at'] = u['created_at'].isoformat()
    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True, port=5000)


