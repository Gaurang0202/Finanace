# Wealthr — Personal Finance Dashboard

A full-stack personal finance management web app: track income and expenses, plan monthly budgets, set savings goals, visualize spending with interactive charts, export reports, and get plain-English AI-style insights about your money.

Built with **Flask 3 / Python 3.13**, **SQLAlchemy**, **Bootstrap 5**, and **Chart.js**.

---

## Features

- **Auth** — registration, login/logout, forgot/reset password, bcrypt password hashing, CSRF-protected forms
- **Dashboard** — balance, monthly income/expense, budget status, recent transactions, goals, AI insights
- **Income & Expense tracking** — full CRUD, search, filter by category, sort, pagination
- **Budget planner** — per-category monthly limits with live progress bars and 80%/100% alerts
- **Savings goals** — target amount, contributions, automatic completion detection
- **Analytics** — income vs expense, spending by category, savings trend, yearly comparison (Chart.js, fed by a small JSON API)
- **Reports** — CSV, Excel (openpyxl) and PDF (ReportLab) exports for any month or year
- **AI-style insights** — a transparent, rule-based engine (pandas) that surfaces spending trends, savings rate, and anomalies in plain English
- **Notifications** — budget warnings, large-expense alerts, goal-achieved messages
- **Profile** — avatar upload, currency preference, password change, light/dark theme
- **Admin panel** — user directory (activate/deactivate), global category management, log viewer
- **Security** — bcrypt hashing, CSRF protection (Flask-WTF), server-side validation, per-user data scoping on every query, environment-based secrets

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Flask-Mail |
| Data / Reports | Pandas, NumPy, openpyxl, ReportLab |
| Frontend | HTML5, Bootstrap 5, Chart.js, Font Awesome, SweetAlert2, Animate.css |
| Database | SQLite by default (zero setup) — swap to PostgreSQL via one `.env` line |

---

## Folder Structure

```
Personal-Finance-Dashboard/
├── app.py                  # Application factory + entry point
├── config.py                # Environment-driven configuration
├── extensions.py            # Shared Flask extension instances
├── forms.py                 # Flask-WTF forms
├── requirements.txt
├── .env.example              # Copy to .env and fill in
├── models/                  # SQLAlchemy models (User, Income, Expense, Budget, ...)
├── routes/                  # Blueprints (auth, dashboard, income, expenses, budget,
│                             #   savings, analytics, api, reports, profile, admin, ...)
├── services/                 # insights.py (AI-style analysis), report_generator.py
├── utils/                    # decorators.py (admin_required, etc.)
├── templates/                # Jinja2 templates, mirrors the blueprint structure
├── static/
│   ├── css/style.css          # Design system (light/dark, tokens, components)
│   └── js/{main.js,charts.js}
└── database/                 # SQLite file + app.log land here at runtime
```

---

## Presentation / Demo Account

A fully populated demo account is created automatically the first time the app starts (idempotent — it's never regenerated once it exists, and it is intentionally **not** reachable via the public registration form):

- **Email:** `presentation@wealthr.com`
- **Password:** `Presentation@123`

The account is self-healing: it's created on every launch method (`python app.py`, `flask run`, gunicorn), older databases get the new columns added automatically, and if the account is deactivated, has its password changed, or has its data deleted, it is repaired or rebuilt on the next start. Data lives in `database/finance.db` — deleting that file (or running from a fresh folder) just produces a fresh copy of the demo account.

It comes pre-loaded with a realistic year of data: 12 months of salary plus freelance/bonus/investment/cashback/interest income, hundreds of categorized expenses (rent, groceries, dining, transport, subscriptions, travel, etc.), 12 monthly budgets spanning under/near/over status, 4 savings goals, and 20 notifications. The current month's income (₹112,500), expenses (₹68,430) and ~39% savings rate are pinned exactly to make the dashboard's headline numbers presentation-ready; the rest of the year uses a seeded random generator, so totals vary run-to-run only if the account is deleted and recreated (the seed is fixed, so a rebuild produces the same data).

## Onboarding Tour

New accounts (and only new accounts) see an interactive spotlight-style product tour on their first visit to the dashboard, highlighting the sidebar, overview, primary "Add Expense" action, notifications, and profile/settings. Completion is stored on the user record itself (`onboarding_completed`), not in browser storage, so it persists across devices. Anyone can replay it anytime from **Profile → Help → Replay Product Tour**.

## Dark Mode & Loading Experience

Dark mode is a real multi-level design system (background → surface → elevated surface → hover/active states), not an inverted palette, and it's synced to Bootstrap's own `data-bs-theme` attribute so native Bootstrap components (alerts, modals, pagination, the close button) pick it up automatically instead of leaking their default light styling. Native browser chrome (scrollbars, date pickers, `<select>` popups) is switched via the CSS `color-scheme` property, and the one third-party popup library in use (SweetAlert2) is explicitly re-themed for dark mode.

Chart data (the dashboard sparkline and the four analytics charts) is fetched client-side after the page loads, so those areas use a shared timed-loading helper (`static/js/loading.js`): nothing is shown for the first ~250ms (no flicker on fast connections), a skeleton appears after that, a contextual message appears at 2s, and "this is taking a little longer than usual" appears at 5s — never a fake error just because the network is slow. A global offline/reconnect banner (bottom of screen, works on every page) detects real connection loss and lets the user retry. Login/register/save/delete buttons show an inline loading state and are guarded against double-submits. The rest of the app is server-rendered in one response per page (a deliberate choice for a Flask app — it avoids the client-side fetch waterfall a shell-then-content architecture would introduce), so page loads themselves are already fast and complete; the loading system focuses on the pieces that are genuinely asynchronous.

## Getting Started

### 1. Clone and set up a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum a real `SECRET_KEY`. The app works out of the box with a local SQLite database — no further setup needed. To use **PostgreSQL** instead, uncomment and edit the `DATABASE_URL` line:

```
DATABASE_URL=postgresql+psycopg://finance_user:finance_pass@localhost:5432/finance_db
```

### 4. Run the app

```bash
python app.py
```

On first run the app automatically creates all tables, seeds the default income/expense categories, and creates a bootstrap admin account (`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`, defaults to `admin@example.com` / `Admin@12345` — **change this in production**).

Visit **http://localhost:5000**.

> **Note on migrations:** the app calls `db.create_all()` on startup, so `flask db upgrade` isn't required for a fresh install. Flask-Migrate is included and wired up (`flask db init / migrate / upgrade`) for when you need real schema migrations as the project evolves.

### 5. Log in

- Create your own account via **Register**, or
- Log in as the seeded admin to access `/admin`.

---

## API Documentation (internal JSON endpoints)

Used by the Analytics page; all require an authenticated session.

| Endpoint | Description |
|---|---|
| `GET /api/charts/income-vs-expense` | Last 6 months of income vs expense totals |
| `GET /api/charts/spending-by-category` | All-time expense totals grouped by category |
| `GET /api/charts/savings-trend` | Net savings (income − expense) for the last 12 months |
| `GET /api/charts/yearly-comparison` | Income vs expense totals grouped by year |

Report downloads: `GET /reports/download/<csv|excel|pdf>?year=YYYY&month=MM` (month optional — omit for a full-year report).

---

## Security Notes

- Passwords are hashed with **bcrypt**, never stored in plain text.
- All forms are protected with **CSRF tokens** (Flask-WTF `CSRFProtect`).
- Every query is scoped to `current_user.id` — one user can never read or modify another's data.
- Admin-only routes are guarded by `@admin_required` on top of `@login_required`.
- Secrets (SECRET_KEY, DB credentials, mail credentials) live only in `.env`, which is git-ignored.

---

## Future Enhancements

- Bank statement (CSV) import and OCR receipt scanning
- Recurring transactions
- Investment portfolio tracker
- Multi-currency conversion
- Scheduled monthly email reports (Flask-Mail is already wired up)
- Google OAuth login
- Dockerfile + docker-compose for one-command deployment

---

## License

MIT — free to use for learning, portfolios, and coursework.
