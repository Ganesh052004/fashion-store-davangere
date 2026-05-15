# 🛍️ LUXE Fashion Store — Fullstack

A complete fashion e-commerce app with Flask backend + vanilla HTML/CSS/JS frontend.

---

## 📁 Project Structure

```
luxe-fullstack/
├── backend/
│   ├── app.py              ← Flask API server
│   ├── requirements.txt    ← Python dependencies
│   └── create_admin.py     ← One-time admin setup helper
├── frontend/
│   ├── login.html          ← Login / Register page  ← OPEN THIS FIRST
│   ├── user.html           ← Customer shopping page
│   └── admin.html          ← Admin dashboard
└── sql/
    └── luxe_db.sql         ← Database schema + seed data
```

---

## 🚀 Setup (Step by Step)

### Step 1 — Install XAMPP & Start MySQL
1. Download XAMPP from https://www.apachefriends.org
2. Open XAMPP Control Panel → Start **MySQL** (Apache is optional)

### Step 2 — Import the Database
**Option A — phpMyAdmin (easiest):**
1. Open http://localhost/phpmyadmin
2. Click **Import** tab → Choose file → select `sql/luxe_db.sql` → **Go**

**Option B — Terminal:**
```bash
mysql -u root < sql/luxe_db.sql
```

### Step 3 — Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 4 — Fix Admin Password (Important!)
```bash
cd backend
python create_admin.py
```
This sets the admin password to **admin123** with a fresh hash.

### Step 5 — Run the Backend
```bash
cd backend
python app.py
```
You should see: `Running on http://127.0.0.1:5000`

### Step 6 — Open the Frontend
Double-click `frontend/login.html` in your file explorer.

---

## 🔑 Default Login

| Role  | Email             | Password  |
|-------|-------------------|-----------|
| Admin | admin@luxe.com    | admin123  |

Register any new account to use the customer/user view.

---

## ✨ Features

- JWT authentication (login / register)
- Customer: browse products, search, filter by category, cart, checkout
- Admin: dashboard stats, manage products (add/edit/delete), view orders & users
- Dark luxury UI with gold accents

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Can't connect to MySQL` | Make sure XAMPP MySQL is running |
| `Access denied for user 'root'` | In `app.py`, update `password=''` to your MySQL root password |
| Admin login fails | Run `python create_admin.py` to reset the hash |
| Blank page / JS error | Make sure backend is running on port 5000 first |
