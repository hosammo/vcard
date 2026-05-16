# VCard SaaS & CMS Overhaul — Design Spec
**Date:** 2026-05-16  
**Status:** Approved  
**Scope:** uv migration, package updates, Wagtail CMS as root, homepage redesign, full marketing site

---

## 1. Goals

Turn VCard into a credible, revenue-ready SaaS by:

1. Modernising the toolchain (uv + pyproject.toml, updated packages)
2. Giving non-developers full editorial control of the marketing site via Wagtail CMS
3. Replacing the outdated homepage with a clean, professional B-style design that converts visitors into signups
4. Building out the full public marketing site (blog, about, pricing, legal) — all CMS-managed

Stripe billing integration is **out of scope** for this phase and will be a separate spec.

---

## 2. Target Audience

Three tiers, each served by an existing plan:

| Segment | Plan | Cards | Key value |
|---------|------|-------|-----------|
| Individual professionals | Free / Pro | 1–5 | Personal networking, NFC sharing |
| Small business owners | Pro / Business | 5–unlimited | Team cards, analytics |
| Companies / agencies | Business | Unlimited | Team mgmt, branded cards, seats |

---

## 3. Architecture

### 3.1 URL Routing

Wagtail owns all public marketing URLs. The Django SaaS app owns all authenticated/functional routes. Both live in a single Django project.

```
/                   → Wagtail CMS (HomePage)
/blog/              → Wagtail (BlogIndexPage)
/blog/<slug>/       → Wagtail (BlogPostPage)
/about/             → Wagtail (AboutPage)
/pricing/           → Wagtail (PricingPage)
/privacy/           → Wagtail (LegalPage)
/terms/             → Wagtail (LegalPage)

/dashboard/         → Django SaaS app
/login/             → Django SaaS app
/register/          → Django SaaS app
/cards/             → Django SaaS app
/api/               → Django REST API
/cms/               → Wagtail admin
/admin/             → Django admin
```

### 3.2 URL Precedence

In `vcard_project/urls.py`, Wagtail's `serve` view is registered **after** all Django app URLs and **before** the Wagtail admin. This ensures `/dashboard/`, `/login/`, etc. are never intercepted by Wagtail.

```python
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cms/', include(wagtailadmin_urls)),      # Wagtail admin
    path('documents/', include(wagtaildocs_urls)), # Wagtail document downloads
    path('', include('cards.urls')),               # SaaS app (dashboard, auth, cards)
    path('', include(wagtail_urls)),               # Wagtail pages — catch-all, must be last
]
```

---

## 4. Workstream 1 — uv Migration & Package Updates

### 4.1 What changes

- Remove `requirements.txt` and `requirements-local.txt`
- Add `pyproject.toml` as the single source of truth for dependencies
- Generate `uv.lock` for reproducible installs
- Install `uv` globally (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 4.2 pyproject.toml structure

```toml
[project]
name = "vcard"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "django>=5.2,<6",
    "djangorestframework>=3.17",
    "wagtail>=6.4",
    "pillow>=12",
    "qrcode[pil]>=8.2",
    "python-decouple>=3.8",
    "psycopg2-binary>=2.9.12",
    "vobject>=0.9.6",
    "gunicorn>=26",
    "whitenoise>=6.7",
    "requests>=2.34",
    "django-crispy-forms>=2.6",
    "crispy-bootstrap5>=2026.3",
    "python-slugify>=8",
    "stripe>=11",
]

[dependency-groups]
dev = [
    "django-debug-toolbar>=4",
    "python-dotenv>=1.2",
]
```

### 4.3 Package versions to update

| Package | Current | Target |
|---------|---------|--------|
| Django | 5.1.4 | 5.2 LTS |
| Wagtail | 6.3 | 6.4 |
| Pillow | 10.4 | 12.x |
| djangorestframework | 3.15.2 | 3.17.x |
| gunicorn | 21.2 | 26.x |
| django-crispy-forms | 2.3 | 2.6 |
| crispy-bootstrap5 | 2024.10 | 2026.3 |
| requests | 2.31 | 2.34 |
| qrcode | 8.0 | 8.2 |
| stripe | 11.4 | 11.x (hold — Stripe spec pending) |

### 4.4 Developer workflow after migration

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv and install all deps
uv sync

# Add a new package
uv add <package>

# Add a dev-only package
uv add --group dev <package>

# Run Django
uv run python manage.py runserver
```

---

## 5. Workstream 2 — Wagtail CMS Setup

### 5.1 New app

Create a `cms` Django app at `cms/` to house all Wagtail page models. This keeps Wagtail models cleanly separated from the `cards` SaaS app.

```
cms/
  __init__.py
  apps.py
  models.py        # All Page subclasses
  blocks.py        # StreamField block definitions
  templates/
    cms/
      home_page.html
      blog_index_page.html
      blog_post_page.html
      about_page.html
      pricing_page.html
      legal_page.html
      base.html        # shared marketing base template
```

### 5.2 Page models

**HomePage**
- `hero_heading` (CharField)
- `hero_subtext` (RichTextField)
- `hero_badge_text` (CharField)
- `features` (StreamField of FeatureBlock)
- `steps` (StreamField of StepBlock)
- `testimonials` (StreamField of TestimonialBlock)
- `cta_heading` (CharField)
- `cta_subtext` (CharField)

**BlogIndexPage**
- `intro` (RichTextField)
- Subpages: BlogPostPage

**BlogPostPage**
- `author` (CharField)
- `published_date` (DateField)
- `hero_image` (Image)
- `body` (StreamField — headings, paragraphs, images, code blocks)
- `excerpt` (TextField)

**AboutPage**
- `body` (StreamField)

**PricingPage**
- `heading` (CharField)
- `subtext` (CharField)
- `tiers` (StreamField of PricingTierBlock)
- `faq` (StreamField of FAQBlock)

**LegalPage**
- `body` (RichTextField — full markdown/HTML legal content)
- Used for both Privacy Policy and Terms of Service

### 5.3 StreamField blocks

```python
# blocks.py
FeatureBlock      # icon (emoji/char), title, description
StepBlock         # number (auto), title, description
TestimonialBlock  # quote, author_name, author_role, avatar (Image)
PricingTierBlock  # name, price, period, features (ListBlock), is_popular, cta_label, cta_url
FAQBlock          # question, answer (RichText)
```

### 5.4 Wagtail settings

- Wagtail site name: `VCard`
- Wagtail admin URL: `/cms/`
- Wagtail search backend: database (default, no Elasticsearch needed at this scale)
- Images: stored in `MEDIA_ROOT/cms/` — same local storage as existing media

### 5.5 Initial page tree (seeded via data migration)

```
Root
└─ VCard (Site root)
   ├─ Home (HomePage) — /
   ├─ Blog (BlogIndexPage) — /blog/
   ├─ About (AboutPage) — /about/
   ├─ Pricing (PricingPage) — /pricing/
   ├─ Privacy Policy (LegalPage) — /privacy/
   └─ Terms of Service (LegalPage) — /terms/
```

---

## 6. Workstream 3 — Homepage Redesign

### 6.1 Design direction

**B — Clean & Minimal (Light)**

- Background: `#ffffff`
- Text: `#111827` (near-black)
- Accent: `#6366f1` (indigo) for highlights and gradient text
- Secondary text: `#6b7280` (gray)
- Cards/sections: `#f9fafb` (off-white)
- Borders: `#f3f4f6` / `#e5e7eb`
- Fonts: system-ui (`-apple-system, BlinkMacSystemFont, 'Segoe UI'`)

### 6.2 Homepage sections (in order)

| # | Section | Content source |
|---|---------|---------------|
| 1 | Sticky nav | Logo, Features, Pricing, Blog, About + Sign In + Get Started CTA | Hardcoded template |
| 2 | Hero | Badge, H1 with gradient accent word, subtext, 2 CTA buttons, social proof (avatar row + user count) | `HomePage` StreamField |
| 3 | Trusted-by strip | 5 company name placeholders | `HomePage` StreamField |
| 4 | Features | 6 feature cards (icon, title, description) | `FeatureBlock` × 6 |
| 5 | How it works | 3-step process with connecting dashed line | `StepBlock` × 3 |
| 6 | Pricing | 3 tiers (Free / Pro / Business) displayed inline with feature lists and CTA buttons; "See full comparison" link goes to `/pricing/` | `PricingTierBlock` data from `PricingPage`, fetched via context |
| 7 | Testimonials | 3 quote cards | `TestimonialBlock` × 3 |
| 8 | CTA banner | Dark bg, headline, subtext, primary CTA | `HomePage` fields |
| 9 | Footer | 4-column: brand + product + company + legal links, socials, copyright | Shared base template |

### 6.3 Template approach

- `cms/templates/cms/base.html` — shared nav + footer for all marketing pages
- `cms/templates/cms/home_page.html` — extends base, renders all hero/features/pricing/testimonials sections
- The existing `cards/templates/auth/base.html` is untouched — used only for dashboard/auth pages

### 6.4 Nav links

```
Features  →  /#features  (anchor on homepage)
Pricing   →  /pricing/   (Wagtail PricingPage)
Blog      →  /blog/      (Wagtail BlogIndexPage)
About     →  /about/     (Wagtail AboutPage)
Sign In   →  /login/
Get Started → /register/
```

---

## 7. Workstream 4 — Remaining Marketing Pages

### 7.1 Blog

- `BlogIndexPage` lists all `BlogPostPage` children, paginated 10/page
- `BlogPostPage` renders with title, author, date, hero image, and rich body content
- Initial content: 0 posts (editor creates first posts via `/cms/`)

### 7.2 About page

- Single `AboutPage` with a StreamField body
- Editor writes the company story, mission, and team section entirely in Wagtail

### 7.3 Pricing page

- Standalone `PricingPage` at `/pricing/` with full tier comparison table and FAQ section
- Pricing data is editable via Wagtail — no code change needed to update prices
- CTA buttons link to `/register/?plan=pro` etc. for pre-selecting a plan on signup

### 7.4 Legal pages

- Two `LegalPage` instances: Privacy Policy at `/privacy/`, Terms of Service at `/terms/`  
- Initial content: placeholder text (editor fills in final copy)
- Footer links point to these pages

---

## 8. Workstream 5 — Dev Branch & Auto-Deployment

### 8.1 Git branch strategy

| Branch | Purpose | Deployed to |
|--------|---------|-------------|
| `main` | Production-ready code | `hosammo.com/vcard/` (manual for now) |
| `dev` | Active development | `devvcard.hosammo.com` (auto on push) |

- All new work happens on `dev`
- `dev` is created from current `main` as first step
- Merging `dev` → `main` triggers nothing automatically (production deploy stays manual this phase)

### 8.2 Server setup (one-time, manual)

On the hosting cPanel:
1. Create subdomain `devvcard.hosammo.com` pointing to `public_html/devvcard/`
2. Clone the repo into `~/devvcard/` via SSH: `git clone https://github.com/hosammo/vcard.git ~/devvcard && cd ~/devvcard && git checkout dev`
3. Create `~/devvcard/.env` with dev-environment values (see 8.4)
4. Create `~/devvcard/passenger_wsgi.py` pointing to the dev settings module
5. Run initial setup: `uv sync && python manage.py migrate && python manage.py collectstatic --noinput`
6. Add SSH public key from GitHub Actions secret to `~/.ssh/authorized_keys`

### 8.3 GitHub Actions workflow

File: `.github/workflows/deploy-dev.yml`

```yaml
name: Deploy to devvcard.hosammo.com

on:
  push:
    branches: [dev]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEV_SSH_HOST }}
          username: ${{ secrets.DEV_SSH_USER }}
          key: ${{ secrets.DEV_SSH_KEY }}
          port: ${{ secrets.DEV_SSH_PORT }}
          script: |
            cd ~/devvcard
            git pull origin dev
            uv sync --frozen
            uv run python manage.py migrate --settings=vcard_project.settings_dev
            uv run python manage.py collectstatic --noinput --settings=vcard_project.settings_dev
            touch tmp/restart.txt
            echo "✅ Dev deploy complete"
```

### 8.4 GitHub Actions secrets required

| Secret | Value |
|--------|-------|
| `DEV_SSH_HOST` | Server hostname or IP |
| `DEV_SSH_USER` | SSH username (cPanel username) |
| `DEV_SSH_KEY` | Private SSH key (generate a dedicated deploy keypair) |
| `DEV_SSH_PORT` | SSH port (usually `22`) |

### 8.5 Dev settings module

File: `vcard_project/settings_dev.py`

```python
from .settings import *

DEBUG = True
ALLOWED_HOSTS = ['devvcard.hosammo.com']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_dev.sqlite3',
    }
}
STATIC_ROOT = BASE_DIR / 'static_collected'
MEDIA_ROOT = BASE_DIR / 'media'
```

Values loaded from `~/devvcard/.env` via `python-decouple` (already in the project).

### 8.6 passenger_wsgi.py for dev

```python
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'vcard_project.settings_dev'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## 9. Implementation Order

```
Phase A  Create dev branch from main + push to GitHub
Phase B  uv install + pyproject.toml migration (on dev branch)
Phase C  Package updates + verify app still runs
Phase D  Create cms/ app + Wagtail page models + URL wiring
Phase E  Seed initial page tree via data migration
Phase F  Build cms/base.html (nav + footer)
Phase G  Build home_page.html (all 9 sections, B-style)
Phase H  Build blog_index_page.html + blog_post_page.html
Phase I  Build about_page.html + pricing_page.html + legal_page.html
Phase J  Add settings_dev.py + GitHub Actions workflow file
Phase K  Server setup: subdomain, clone repo, initial deploy (manual SSH)
Phase L  Smoke-test devvcard.hosammo.com + verify auto-deploy on push
```

---

## 10. Out of Scope (Next Phase)

- Stripe billing (real payment processing)
- Email service integration (SendGrid / Mailgun)
- Cloud file storage (S3)
- Email verification on signup
- Redis caching for geolocation
- 2FA / social login
- Custom domains

---

## 11. Constraints & Assumptions

- Django version bumped to **5.2 LTS** (not 6.x — too many breaking changes)
- Wagtail 6.4 is compatible with Django 5.2
- SQLite remains the database for development; no DB changes needed for this phase
- Existing `cards/` app is untouched — no SaaS feature regressions
- `uv` replaces `pip` and `venv` entirely; no `requirements.txt` files remain after migration
- `.gitignore` updated to exclude `uv.lock` from tracking? No — `uv.lock` **should** be committed for reproducibility
