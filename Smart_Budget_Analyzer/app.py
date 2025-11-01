from flask import Flask, render_template, request, redirect, url_for
import json
import os
from collections import defaultdict

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    expenses = load_data()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Uncategorized').strip()
    try:
        amount = float(request.form.get('amount', '0'))
    except ValueError:
        amount = 0.0

    if not name or amount <= 0:
        return redirect(url_for('index'))

    data = load_data()
    data.append({'name': name, 'category': category, 'amount': amount})
    save_data(data)
    return redirect(url_for('index'))

@app.route('/analyze')
def analyze():
    data = load_data()
    if not data:
        return render_template('analyze.html', message="No expenses yet. Add some and come back for analysis.")

    total = sum(item['amount'] for item in data)
    count = len(data)
    overall_avg = round(total / count, 2) if count else 0.0

    # Per-category totals and averages
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    for item in data:
        cat = item.get('category', 'Uncategorized')
        amt = item.get('amount', 0)
        category_totals[cat] += amt
        category_counts[cat] += 1

    per_category = []
    for cat, amt in category_totals.items():
        cnt = category_counts[cat]
        avg = round(amt / cnt, 2) if cnt else 0.0
        percent = round((amt / total) * 100, 2) if total else 0.0
        per_category.append({'category': cat, 'amount': round(amt,2), 'count': cnt, 'avg': avg, 'percent': percent})

    # Insights / suggestions
    suggestions = []
    # Overspending category (more than 40%)
    max_cat = max(category_totals, key=category_totals.get)
    if category_totals[max_cat] > 0.4 * total:
        suggestions.append(f"You spent ₹{round(category_totals[max_cat],2)} on '{max_cat}', which is over 40% of your total spending. Consider reducing it.")

    # High average item suggestion
    high_avg = [c for c in per_category if c['avg'] > overall_avg * 1.5]
    for c in high_avg:
        suggestions.append(f"Average expense in category '{c['category']}' is ₹{c['avg']}, which is significantly higher than overall average ₹{overall_avg}.")

    # Small saving tip: suggest saving 10% of total
    suggested_saving = round(0.1 * total, 2)
    suggestions.append(f"Try to save at least ₹{suggested_saving} (10% of total) next period.")

    # Sort per_category by amount descending
    per_category_sorted = sorted(per_category, key=lambda x: x['amount'], reverse=True)

    return render_template('analyze.html',
                           total=round(total,2),
                           overall_avg=overall_avg,
                           per_category=per_category_sorted,
                           suggestions=suggestions)

if __name__ == '__main__':
    # ensure data file exists
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    app.run(debug=True)