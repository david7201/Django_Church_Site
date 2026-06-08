from django.conf import settings
from django.core.mail import EmailMessage


def send_church_notification(subject, body, reply_to=None):
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CHURCH_NOTIFICATION_EMAIL],
        reply_to=[reply_to] if reply_to else None,
    )
    return message.send()


def send_request_reply(recipient, subject, body):
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[settings.CHURCH_NOTIFICATION_EMAIL],
    )
    return message.send()
