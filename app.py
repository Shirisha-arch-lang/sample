from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import sqlite3
import os
from datetime import datetime, date, timedelta
from functools import wraps
import json
import csv
import io

app = Flask(__name__)
app.secret_key = 'smartexpense_secret_2024'
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'db.sqlite3')

# ─── DB SETUP ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            is_recurring INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            saved_amount REAL DEFAULT 0,
            deadline TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', (name, email, password))
            conn.commit()
            # Insert sample data for demo
            user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
            seed_sample_data(conn, user['id'])
            conn.close()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def seed_sample_data(conn, user_id):
    today = date.today()
    categories = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Others']
    import random
    random.seed(42)
    for i in range(60):
        d = today - timedelta(days=i)
        cat = random.choice(categories)
        amt = round(random.uniform(50, 2000), 2)
        desc_map = {'Food':'Restaurant/Grocery','Transport':'Cab/Bus','Shopping':'Online/Retail',
                    'Bills':'Electricity/Internet','Entertainment':'Movies/OTT','Health':'Pharmacy/Clinic','Others':'Miscellaneous'}
        conn.execute('INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?,?,?,?,?)',
                     (user_id, amt, cat, d.strftime('%Y-%m-%d'), desc_map[cat]))
    # Budget
    conn.execute('INSERT INTO budgets (user_id, month, amount) VALUES (?,?,?)',
                 (user_id, today.strftime('%Y-%m'), 20000))
    # Savings goal
    conn.execute('INSERT INTO savings_goals (user_id, title, target_amount, saved_amount, deadline) VALUES (?,?,?,?,?)',
                 (user_id, 'Emergency Fund', 50000, 18500, (today + timedelta(days=180)).strftime('%Y-%m-%d')))
    conn.execute('INSERT INTO savings_goals (user_id, title, target_amount, saved_amount, deadline) VALUES (?,?,?,?,?)',
                 (user_id, 'Vacation', 30000, 8000, (today + timedelta(days=90)).strftime('%Y-%m-%d')))
    conn.commit()

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    conn = get_db()
    today = date.today()
    month_str = today.strftime('%Y-%m')

    total = conn.execute('SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=?', (uid,)).fetchone()['s']
    monthly = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date LIKE ?",
                           (uid, month_str+'%')).fetchone()['s']
    budget_row = conn.execute('SELECT amount FROM budgets WHERE user_id=? AND month=?', (uid, month_str)).fetchone()
    budget = budget_row['amount'] if budget_row else 0
    top_cat = conn.execute("SELECT category, SUM(amount) as s FROM expenses WHERE user_id=? AND date LIKE ? GROUP BY category ORDER BY s DESC LIMIT 1",
                           (uid, month_str+'%')).fetchone()
    days_in_month = today.day
    avg_daily = round(monthly / days_in_month, 2) if days_in_month else 0
    recent = conn.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC LIMIT 5", (uid,)).fetchall()
    goals = conn.execute('SELECT * FROM savings_goals WHERE user_id=?', (uid,)).fetchall()
    conn.close()

    remaining = max(0, budget - monthly)
    budget_pct = min(100, round((monthly / budget * 100) if budget else 0, 1))
    insights = generate_insights(uid)

    return render_template('dashboard.html',
        total=total, monthly=monthly, budget=budget, remaining=remaining,
        budget_pct=budget_pct, top_cat=top_cat, avg_daily=avg_daily,
        recent=recent, goals=goals, insights=insights,
        user_name=session['user_name'])

# ─── EXPENSES ────────────────────────────────────────────────────────────────

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    uid = session['user_id']
    if request.method == 'POST':
        conn = get_db()
        conn.execute('INSERT INTO expenses (user_id,amount,category,date,description,is_recurring) VALUES (?,?,?,?,?,?)',
                     (uid, request.form['amount'], request.form['category'],
                      request.form['date'], request.form.get('description',''),
                      1 if request.form.get('recurring') else 0))
        conn.commit()
        conn.close()
        flash('Expense added!', 'success')
        return redirect(url_for('expenses'))

    conn = get_db()
    q = "SELECT * FROM expenses WHERE user_id=?"
    params = [uid]
    cat = request.args.get('category','')
    date_from = request.args.get('date_from','')
    date_to = request.args.get('date_to','')
    search = request.args.get('search','')
    if cat: q += ' AND category=?'; params.append(cat)
    if date_from: q += ' AND date>=?'; params.append(date_from)
    if date_to: q += ' AND date<=?'; params.append(date_to)
    if search: q += ' AND description LIKE ?'; params.append(f'%{search}%')
    q += ' ORDER BY date DESC'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return render_template('expenses.html', expenses=rows, cat=cat, date_from=date_from, date_to=date_to, search=search)

@app.route('/expense/edit/<int:eid>', methods=['GET', 'POST'])
@login_required
def edit_expense(eid):
    uid = session['user_id']
    conn = get_db()
    exp = conn.execute('SELECT * FROM expenses WHERE id=? AND user_id=?', (eid, uid)).fetchone()
    if not exp:
        conn.close(); return redirect(url_for('expenses'))
    if request.method == 'POST':
        conn.execute('UPDATE expenses SET amount=?,category=?,date=?,description=? WHERE id=?',
                     (request.form['amount'], request.form['category'], request.form['date'],
                      request.form.get('description',''), eid))
        conn.commit()
        conn.close()
        flash('Expense updated!', 'success')
        return redirect(url_for('expenses'))
    conn.close()
    return render_template('edit_expense.html', exp=exp)

@app.route('/expense/delete/<int:eid>')
@login_required
def delete_expense(eid):
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM expenses WHERE id=? AND user_id=?', (eid, uid))
    conn.commit()
    conn.close()
    flash('Expense deleted.', 'success')
    return redirect(url_for('expenses'))

# ─── ANALYTICS ───────────────────────────────────────────────────────────────

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/api/chart-data')
@login_required
def chart_data():
    uid = session['user_id']
    conn = get_db()
    today = date.today()

    # Pie: category
    cat_rows = conn.execute(
        "SELECT category, SUM(amount) as s FROM expenses WHERE user_id=? AND date>=? GROUP BY category",
        (uid, (today - timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()
    pie = {'labels': [r['category'] for r in cat_rows], 'data': [round(r['s'],2) for r in cat_rows]}

    # Bar: monthly (last 6 months)
    bar_labels, bar_data = [], []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*28)
        m = d.strftime('%Y-%m')
        row = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date LIKE ?",
                           (uid, m+'%')).fetchone()
        bar_labels.append(d.strftime('%b %Y'))
        bar_data.append(round(row['s'], 2))

    # Line: daily last 30 days
    line_labels, line_data = [], []
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        row = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date=?", (uid, d)).fetchone()
        line_labels.append(d[5:])
        line_data.append(round(row['s'], 2))

    conn.close()
    return jsonify({'pie': pie, 'bar': {'labels': bar_labels, 'data': bar_data},
                    'line': {'labels': line_labels, 'data': line_data}})

# ─── BUDGET ──────────────────────────────────────────────────────────────────

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    uid = session['user_id']
    conn = get_db()
    today = date.today()
    month_str = today.strftime('%Y-%m')
    if request.method == 'POST':
        amt = float(request.form['amount'])
        existing = conn.execute('SELECT id FROM budgets WHERE user_id=? AND month=?', (uid, month_str)).fetchone()
        if existing:
            conn.execute('UPDATE budgets SET amount=? WHERE user_id=? AND month=?', (amt, uid, month_str))
        else:
            conn.execute('INSERT INTO budgets (user_id,month,amount) VALUES (?,?,?)', (uid, month_str, amt))
        conn.commit()
        flash('Budget updated!', 'success')

    budget_row = conn.execute('SELECT amount FROM budgets WHERE user_id=? AND month=?', (uid, month_str)).fetchone()
    budget = budget_row['amount'] if budget_row else 0
    monthly = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date LIKE ?",
                           (uid, month_str+'%')).fetchone()['s']
    cat_rows = conn.execute("SELECT category, SUM(amount) as s FROM expenses WHERE user_id=? AND date LIKE ? GROUP BY category",
                            (uid, month_str+'%')).fetchall()
    goals = conn.execute('SELECT * FROM savings_goals WHERE user_id=?', (uid,)).fetchall()
    conn.close()
    remaining = max(0, budget - monthly)
    budget_pct = min(100, round((monthly / budget * 100) if budget else 0, 1))
    return render_template('budget.html', budget=budget, monthly=monthly, remaining=remaining,
                           budget_pct=budget_pct, cat_rows=cat_rows, goals=goals, month=month_str)

@app.route('/goal/add', methods=['POST'])
@login_required
def add_goal():
    uid = session['user_id']
    conn = get_db()
    conn.execute('INSERT INTO savings_goals (user_id,title,target_amount,saved_amount,deadline) VALUES (?,?,?,?,?)',
                 (uid, request.form['title'], float(request.form['target']),
                  float(request.form.get('saved', 0)), request.form.get('deadline','')))
    conn.commit(); conn.close()
    flash('Goal added!', 'success')
    return redirect(url_for('budget'))

@app.route('/goal/delete/<int:gid>')
@login_required
def delete_goal(gid):
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM savings_goals WHERE id=? AND user_id=?', (gid, uid))
    conn.commit(); conn.close()
    return redirect(url_for('budget'))

# ─── REPORTS ─────────────────────────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC', (uid,)).fetchall()
    conn.close()
    return render_template('reports.html', expenses=rows)

@app.route('/export/csv')
@login_required
def export_csv():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('SELECT date,category,amount,description FROM expenses WHERE user_id=? ORDER BY date DESC', (uid,)).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Amount (₹)', 'Description'])
    for r in rows:
        writer.writerow([r['date'], r['category'], r['amount'], r['description']])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     as_attachment=True, download_name='expenses.csv')

# ─── SETTINGS ────────────────────────────────────────────────────────────────

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    uid = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        conn.execute('UPDATE users SET name=? WHERE id=?', (name, uid))
        conn.commit()
        session['user_name'] = name
        flash('Profile updated!', 'success')
    user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    return render_template('settings.html', user=user)

# ─── INSIGHTS ────────────────────────────────────────────────────────────────

def generate_insights(uid):
    conn = get_db()
    today = date.today()
    this_month = today.strftime('%Y-%m')
    last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

    insights = []
    this = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date LIKE ?",
                        (uid, this_month+'%')).fetchone()['s']
    prev = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND date LIKE ?",
                        (uid, last_month+'%')).fetchone()['s']

    if prev > 0:
        pct = round((this - prev) / prev * 100, 1)
        if pct > 0:
            insights.append({'type':'warning','icon':'📈','text':f'You spent {pct}% more than last month. Consider reviewing discretionary expenses.'})
        else:
            insights.append({'type':'success','icon':'📉','text':f'Great job! You spent {abs(pct)}% less than last month.'})

    top = conn.execute("SELECT category, SUM(amount) as s FROM expenses WHERE user_id=? AND date LIKE ? GROUP BY category ORDER BY s DESC LIMIT 1",
                       (uid, this_month+'%')).fetchone()
    if top:
        insights.append({'type':'info','icon':'🏆','text':f'Your highest spending category is <strong>{top["category"]}</strong> this month.'})

    food = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND category='Food' AND date LIKE ?",
                        (uid, this_month+'%')).fetchone()['s']
    if this > 0 and food / this > 0.35:
        insights.append({'type':'warning','icon':'🍕','text':f'Food accounts for {round(food/this*100)}% of your spending. Consider meal prepping to save.'})

    ent = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=? AND category='Entertainment' AND date LIKE ?",
                       (uid, this_month+'%')).fetchone()['s']
    if ent > 2000:
        insights.append({'type':'danger','icon':'🎬','text':f'Entertainment spending is ₹{ent:.0f}. Try reducing OTT subscriptions or outings.'})

    conn.close()
    if not insights:
        insights.append({'type':'info','icon':'💡','text':'Keep tracking expenses to unlock personalized insights!'})
    return insights

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
