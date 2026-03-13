# CV Portfolio Site

A Flask-based CV portfolio that updates automatically when you upload a `.docx` file. The admin panel parses the document with **Ollama Cloud** (e.g. `gpt-oss:120b`) and saves structured data; the public site renders it with a clean, responsive layout. Admin login is protected with **Google reCAPTCHA v2**.

## Project structure

```
website/
├── app.py                 # Flask app and routes
├── cv_parser.py            # .docx → JSON via Ollama Cloud
├── requirements.txt
├── Dockerfile              # For Docker / docker-compose
├── .env.example            # Copy to .env and fill in
├── data/
│   └── cv.json             # Generated CV data (create via admin upload)
├── uploads/                # Temporary .docx storage
├── templates/
│   ├── index.html          # Public CV + contact form
│   ├── admin.html          # Admin dashboard (upload, preview)
│   └── admin_login.html    # Admin login (password + reCAPTCHA v2)
└── static/
    ├── css/                # style.css, admin.css
    └── js/                 # main.js, admin.js
```

## Setup

### 1. Dependencies

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy the example file and set your values:

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret (long random string) |
| `ADMIN_PASSWORD` | Password for `/admin` login |
| `OLLAMA_API_KEY` | Ollama Cloud API key for CV parsing |
| `OLLAMA_MODEL` | Model name (e.g. `gpt-oss:120b`) |
| `RECAPTCHA_SITE_KEY` | Google reCAPTCHA v2 site key |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v2 secret key |

Optional:

- `OLLAMA_URL` — Ollama API base URL (default: `https://ollama.com`)
- `HOST` — Bind host (default: `127.0.0.1`; use `0.0.0.0` in Docker)
- `PORT` — Port (default: `5000`)

### 3. Run locally

```bash
python app.py
```

- **http://localhost:5000** — public CV and contact form  
- **http://localhost:5000/admin** — redirects to login, then upload/preview

Admin login requires the password from `.env` and a completed reCAPTCHA v2 challenge. If reCAPTCHA keys are missing, the app shows “reCAPTCHA is not configured.”

## Docker

Build and run with Docker:

```bash
docker build -t portfolio .
docker run -p 5000:5000 --env-file .env portfolio
```

Or add this service to an existing `docker-compose.yml`:

```yaml
services:
  portfolio:
    build: ./website
    ports:
      - "5000:5000"
    env_file:
      - ./website/.env
```

The Dockerfile sets `HOST=0.0.0.0` and `PORT=5000` so the app is reachable from the host.

## How it works

1. **Public site** — Renders `data/cv.json` (about, experience, projects, skills, contact). If no CV is uploaded, it shows an empty state with a link to the admin panel.
2. **Admin** — Log in at `/admin/login` (password + reCAPTCHA v2). Then upload a `.docx` CV; the app sends the text to Ollama, gets structured JSON, and writes it to `data/cv.json`. The public site updates on the next request.
3. **Contact form** — POSTs to `/contact` (endpoint is ready; plug in your own mail or API).

## Updating your CV

Go to `/admin`, sign in, and upload a new `.docx`. The site updates immediately; no redeploy needed (unless you run in a fresh container without a volume for `data/`).

## Deployment notes

- Use a production WSGI server (e.g. **gunicorn**): `gunicorn app:app`
- Set a strong `SECRET_KEY` and `ADMIN_PASSWORD`
- Keep `.env` (and reCAPTCHA keys) out of version control; rely on `.env.example` for documentation
- If you persist CV data in Docker, mount a volume for `data/` (and optionally `uploads/`)
