def global_notifications(request):
    if request.user.is_authenticated:
        from notifications.models import Notification

        unread = Notification.objects.filter(recipient=request.user, is_read=False)
        return {
            "global_unread_notification_count": unread.count(),
            "global_recent_notifications": unread.select_related("sender")[:5],
        }
    return {"global_unread_notification_count": 0, "global_recent_notifications": []}
