from notifications.models import Notification


def notify_user(recipient, message, *, sender=None, link=""):
    if recipient is None:
        return None
    if sender is not None and recipient == sender:
        return None
    return Notification.objects.create(recipient=recipient, sender=sender, message=message, link=link)


def notify_users(recipients, message, *, sender=None, link=""):
    notifications = []
    seen = set()
    for recipient in recipients:
        if recipient is None or recipient.pk in seen:
            continue
        if sender is not None and recipient.pk == sender.pk:
            continue
        seen.add(recipient.pk)
        notifications.append(Notification(recipient=recipient, sender=sender, message=message, link=link))
    if notifications:
        Notification.objects.bulk_create(notifications)
    return notifications
