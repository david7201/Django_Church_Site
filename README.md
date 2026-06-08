# Mount Zion Dublin Django Website

Dynamic Django version of the Mount Zion church website. The public site keeps the existing visual theme while allowing church staff to edit content through a friendlier Django admin.

## Main Features

- Editable Home, About, Services, Charity, Building Fund, Events, and Contact pages.
- Admin-addable page sections with draft/published status and public/member-only visibility.
- Bilingual English/Romanian content fields and language switcher.
- Public member signup/login/logout and password reset screens.
- Hidden private admin login and one-time invite-based admin signup.
- Invited staff receive full website-management access but cannot edit, demote, or delete other administrators.
- Default `/admin/` route removed; admin lives under the private `ADMIN_SECRET` path.
- Announcements with urgent banner, start/end dates, and public/member-only visibility.
- Building fund progress bar, giving tiers, milestones, photo updates, and featured homepage update.
- Reusable admin image gallery with upload compression/resizing.
- Events/projects with image slideshows.
- Newsletter signup with categories: General, Fundraising, Youth, Prayer, Services, Building Updates.
- Admin newsletter composer with draft/send workflow and Brevo SMTP delivery.
- Contact and prayer request forms with honeypot spam protection, mailbox notifications, and admin email replies.
- Basic admin audit fields for created/updated user and timestamps.

## Local Docker Setup

Build and start the site:

```powershell
docker compose up -d --build
```

Apply database migrations:

```powershell
docker compose exec web python manage.py migrate
```

The web container also applies pending migrations automatically whenever it starts.

Load starter Mount Zion content:

```powershell
docker compose exec web python manage.py bootstrap_site
```

Open the site:

```text
http://localhost:8000
```

## Admin Access

For development, Docker reads `.env.example`. For real credentials, create `.env`; it will override `.env.example`.

Set a real private admin secret in `.env` before production:

```text
ADMIN_SECRET=your-long-private-random-secret
```

The private admin login path is:

```text
/mz-private-control/<ADMIN_SECRET>/login/
```

The Django admin dashboard path is:

```text
/mz-private-control/<ADMIN_SECRET>/dashboard/
```

Create a one-time admin signup invite:

```powershell
docker compose exec web python manage.py create_admin_invite --email admin@example.com --days 7
```

The command prints the private signup URL.

## Email And Brevo SMTP

Newsletter sending, password resets, request notifications, and admin replies use
the SMTP settings below. Without SMTP credentials, Django falls back to console
email for local development.

Private SMTP credentials must be placed in the ignored `.env` file:

```text
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-brevo-smtp-login
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Mount Zion Church <your-verified-sender@example.com>
SERVER_EMAIL=Mount Zion Church <your-verified-sender@example.com>
CHURCH_NOTIFICATION_EMAIL=church-mailbox@example.com
SITE_URL=https://your-domain.com
```

## Tests

Run tests locally:

```powershell
python manage.py test
```

Run tests in Docker:

```powershell
docker compose run --rm web python manage.py test
```

Run Django checks:

```powershell
python manage.py check
docker compose run --rm web python manage.py check
```
