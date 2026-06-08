from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from church.models import AdminInvite


class Command(BaseCommand):
    help = "Create a one-time private admin signup invite."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="", help="Optional email address this invite is restricted to.")
        parser.add_argument("--days", type=int, default=7, help="Number of days before the invite expires.")

    def handle(self, *args, **options):
        invite = AdminInvite.objects.create(
            email=options["email"].strip().lower(),
            expires_at=timezone.now() + timezone.timedelta(days=options["days"]),
        )
        signup_url = f"{settings.SITE_URL}{invite.get_signup_path()}"
        self.stdout.write(self.style.SUCCESS("Admin invite created."))
        self.stdout.write(signup_url)
