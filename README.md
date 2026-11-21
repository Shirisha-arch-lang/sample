# SpendWise — Smart Expense Tracker

A modern fintech-style personal expense tracking web application built with Flask, SQLite, and Chart.js.

## Features

- **Authentication** — Register, login, logout
- **Expense Management** — Add, edit, delete, filter, search expenses
- **Dashboard Analytics** — Summary cards, budget ring, recent expenses, savings goals
- **Visual Analytics** — Pie (category), Bar (monthly), Line (trend) charts
- **Budget Management** — Set monthly budget, track % used, per-category breakdown
- **Savings Goals** — Goal-based saving tracker with progress bars
- **Smart Insights** — Simulated AI-generated spending tips
- **Reports & Export** — Full expense table + CSV download
- **Sample Data** — 60 auto-generated expenses on registration for demo

## Tech Stack

| Layer      | Technology         |
|------------|--------------------|
| Backend    | Python Flask       |
| Database   | SQLite3            |
| Frontend   | HTML, CSS, JS      |
| Charts     | Chart.js 4.x       |
| Fonts      | Syne + DM Sans     |

## Project Structure

```
expense-tracker/
├── app.py                    # Main Flask app (routes, auth, API)
├── requirements.txt
├── database/
│   └── db.sqlite3            # Auto-created on first run
├── templates/
│   ├── layout.html           # Base layout with sidebar & topbar
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── expenses.html
│   ├── edit_expense.html
│   ├── analytics.html
│   ├── budget.html
│   ├── reports.html
│   └── settings.html
└── static/
    ├── css/style.css         # Full fintech design system
    └── js/
        ├── app.js            # UI helpers
        └── charts.js         # Chart.js chart rendering
```

## Quick Start

```bash
# 1. Install dependencies
pip install flask

# 2. Run the app
python app.py

# 3. Open in browser
# http://localhost:5000
```

## Usage

1. Open `http://localhost:5000`
2. Click **Register** — 60 sample expenses + a ₹20,000 budget are auto-loaded
3. Explore **Dashboard**, **Analytics**, **Budget**, **Reports**
4. Add/edit/delete your own expenses
5. Download CSV from the Reports page

## Design

- **Colors**: Blue primary `#3b82f6`, Success green `#22c55e`, Warning amber `#f59e0b`, Danger red `#ef4444`
- **Fonts**: Syne (display/headings) + DM Sans (body)
- **Style**: Modern fintech dashboard with sidebar, stat cards, gradient badges, animated progress bars
- **Responsive**: Mobile-friendly with collapsible sidebar

## Academic Note

This project is built for academic demonstration. All financial data is either user-entered or randomly generated as sample data. No real financial APIs are connected.
