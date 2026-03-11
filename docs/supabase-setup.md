# Supabase Setup (Flask App)

## 1) Install dependency

```bash
./venv/bin/pip install supabase
```

## 2) Configure environment variables

Set these before running Flask:

```bash
export FLASK_SECRET_KEY="replace-with-strong-random-secret"
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_ANON_KEY="<anon-key>"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
```

`SUPABASE_SERVICE_ROLE_KEY` is reserved for future admin/background operations.

## 3) Create database schema + RLS

Run:

```sql
-- copy/paste docs/supabase-schema.sql into Supabase SQL Editor
```

## 4) Auth provider

In Supabase Dashboard:

- Enable Email auth.
- Set Site URL (local: `http://127.0.0.1:5000`).
- Add Redirect URLs for local/prod environments.

## 5) Run app

```bash
python -m flask --app app run --host 127.0.0.1 --port 5000
```

When `SUPABASE_URL` + `SUPABASE_ANON_KEY` are set, the app uses Supabase for:

- `login` / `signup` / `logout`
- Profile data (`/user`)
- Settings data (`/settings`)
- Boards, cards, and activity APIs
