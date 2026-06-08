from django import template
from django.templatetags.static import static
from django.utils.translation import get_language


register = template.Library()


UI_TEXT = {
    "en": {
        "home": "Home",
        "services": "Services",
        "about": "About",
        "charity": "Charity",
        "building_fund": "Building Fund",
        "events": "Events",
        "contact": "Contact",
        "members": "Members",
        "login": "Login",
        "logout": "Logout",
        "menu": "Menu",
        "view": "View",
        "accept": "Accept",
        "closed": "Closed",
        "church_opening_hours": "Church Opening Hours",
        "raised": "raised",
        "goal": "goal",
        "latest_update": "Latest update",
        "meet_team": "Meet Our Team",
        "subscribe_title": "Subscribe for church updates",
        "subscribe_intro": "Choose the announcements you want: fundraising, youth, prayer, services, and building updates.",
        "name": "Name",
        "email": "Email",
        "language": "Language",
        "choose_updates": "Choose updates",
        "subscribe": "Subscribe",
        "address": "Address",
        "phone": "Phone",
        "support_mission": "Support Our Mission",
        "donation_soon": "Donation details will be added soon.",
        "giving_tiers": "Giving Tiers",
        "construction_timeline": "Construction Timeline",
        "construction_progress": "Construction progress",
        "step": "Step",
        "of": "of",
        "not_started": "Not started",
        "target": "Target",
        "photo_updates": "Photo Updates",
        "building_soon": "Building fund details will be added soon.",
        "give": "Give",
        "events_soon": "Events and church activity updates will be added soon.",
        "send_message": "Send a Message",
        "send_message_button": "Send Message",
        "prayer_request": "Prayer Request",
        "send_prayer_button": "Send Prayer Request",
        "member_updates": "Member Updates",
        "member_updates_subtitle": "Private announcements and updates for signed-in users",
        "announcements": "Announcements",
        "no_member_announcements": "No member announcements yet.",
        "building_updates": "Building Updates",
        "no_building_updates": "No building updates yet.",
        "unsubscribed_title": "You have been unsubscribed",
        "unsubscribed_body": "will no longer receive newsletter emails.",
        "return_home": "Return Home",
        "member_login": "Member Login",
        "member_login_intro": "Sign in to see member-only announcements and updates.",
        "forgot_password": "Forgot password?",
        "create_account_link": "Create account",
        "create_member_account": "Create Member Account",
        "create_member_intro": "Create an account to see updates that are shared only with logged-in users.",
        "create_account_button": "Create Account",
        "already_have_account": "Already have an account?",
        "admin_login": "Website Admin Login",
        "admin_login_intro": "This private page is only for approved Mount Zion website administrators.",
        "login_admin": "Login to Admin",
        "create_admin": "Create Admin Account",
        "create_admin_intro": "This private signup link can be used once before it expires.",
        "create_admin_button": "Create Admin",
        "reset_password": "Reset Password",
        "reset_password_intro": "Enter your email address and we will send a reset link.",
        "send_reset_link": "Send Reset Link",
        "check_email": "Check Your Email",
        "check_email_intro": "If an account exists with that address, a password reset link has been sent.",
        "choose_new_password": "Choose New Password",
        "update_password": "Update Password",
        "invalid_reset_link": "This password reset link is invalid or has expired.",
        "request_new_link": "Request New Link",
        "password_updated": "Password Updated",
        "password_updated_intro": "Your password has been changed. You can now log in.",
    },
    "ro": {
        "home": "Acasă",
        "services": "Servicii",
        "about": "Despre noi",
        "charity": "Caritate",
        "building_fund": "Fondul de construcție",
        "events": "Evenimente",
        "contact": "Contact",
        "members": "Membri",
        "login": "Autentificare",
        "logout": "Ieșire",
        "menu": "Meniu",
        "view": "Vezi",
        "accept": "Accept",
        "closed": "Închis",
        "church_opening_hours": "Programul bisericii",
        "raised": "strânși",
        "goal": "obiectiv",
        "latest_update": "Ultima actualizare",
        "meet_team": "Echipa noastră",
        "subscribe_title": "Abonează-te la noutățile bisericii",
        "subscribe_intro": "Alege anunțurile dorite: strângere de fonduri, tineret, rugăciune, servicii și actualizări despre construcție.",
        "name": "Nume",
        "email": "Email",
        "language": "Limbă",
        "choose_updates": "Alege noutățile",
        "subscribe": "Abonează-te",
        "address": "Adresă",
        "phone": "Telefon",
        "support_mission": "Susține misiunea noastră",
        "donation_soon": "Detaliile pentru donații vor fi adăugate în curând.",
        "giving_tiers": "Niveluri de donație",
        "construction_timeline": "Etapele construcției",
        "construction_progress": "Progresul construcției",
        "step": "Etapa",
        "of": "din",
        "not_started": "Construcția nu a început",
        "target": "Țintă",
        "photo_updates": "Actualizări foto",
        "building_soon": "Detaliile fondului de construcție vor fi adăugate în curând.",
        "give": "Donează",
        "events_soon": "Evenimentele și activitățile bisericii vor fi adăugate în curând.",
        "send_message": "Trimite un mesaj",
        "send_message_button": "Trimite mesajul",
        "prayer_request": "Cerere de rugăciune",
        "send_prayer_button": "Trimite cererea",
        "member_updates": "Actualizări pentru membri",
        "member_updates_subtitle": "Anunțuri și noutăți private pentru utilizatorii autentificați",
        "announcements": "Anunțuri",
        "no_member_announcements": "Nu există încă anunțuri pentru membri.",
        "building_updates": "Actualizări despre construcție",
        "no_building_updates": "Nu există încă actualizări despre construcție.",
        "unsubscribed_title": "Ai fost dezabonat",
        "unsubscribed_body": "nu va mai primi emailuri cu noutăți.",
        "return_home": "Înapoi acasă",
        "member_login": "Autentificare membri",
        "member_login_intro": "Autentifică-te pentru a vedea anunțurile și actualizările doar pentru membri.",
        "forgot_password": "Ai uitat parola?",
        "create_account_link": "Creează cont",
        "create_member_account": "Creează cont de membru",
        "create_member_intro": "Creează un cont pentru a vedea actualizările disponibile doar utilizatorilor autentificați.",
        "create_account_button": "Creează cont",
        "already_have_account": "Ai deja cont?",
        "admin_login": "Autentificare administratori",
        "admin_login_intro": "Această pagină privată este doar pentru administratorii aprobați ai site-ului Mount Zion.",
        "login_admin": "Intră în administrare",
        "create_admin": "Creează cont de administrator",
        "create_admin_intro": "Acest link privat poate fi folosit o singură dată înainte să expire.",
        "create_admin_button": "Creează administrator",
        "reset_password": "Resetare parolă",
        "reset_password_intro": "Introdu adresa de email și îți vom trimite un link de resetare.",
        "send_reset_link": "Trimite linkul",
        "check_email": "Verifică emailul",
        "check_email_intro": "Dacă există un cont cu această adresă, a fost trimis un link de resetare.",
        "choose_new_password": "Alege o parolă nouă",
        "update_password": "Actualizează parola",
        "invalid_reset_link": "Acest link de resetare este invalid sau a expirat.",
        "request_new_link": "Cere un link nou",
        "password_updated": "Parola a fost actualizată",
        "password_updated_intro": "Parola ta a fost schimbată. Acum te poți autentifica.",
    },
}


def active_language():
    return (get_language() or "en").split("-")[0]


@register.filter
def tr(obj, field_name):
    language = active_language()
    translated = getattr(obj, f"{field_name}_{language}", "")
    english = getattr(obj, f"{field_name}_en", "")
    fallback = getattr(obj, field_name, "")
    return translated or english or fallback


@register.simple_tag
def ui(key):
    language = active_language()
    return UI_TEXT.get(language, UI_TEXT["en"]).get(key, UI_TEXT["en"].get(key, key))


@register.simple_tag
def image_source(asset=None, static_path=""):
    if asset and getattr(asset, "image", None):
        return asset.image.url
    if static_path:
        return static(static_path)
    return ""


@register.filter
def split_lines(value):
    if not value:
        return []
    return [line.strip() for line in str(value).splitlines() if line.strip()]


@register.filter
def currency(value):
    if value is None:
        return "€0"
    return f"€{value:,.0f}"


@register.filter
def get_item(mapping, key):
    if not mapping:
        return None
    return mapping.get(key)
