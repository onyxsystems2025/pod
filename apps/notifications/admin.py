from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("shipment", "channel", "recipient", "status", "sent_at", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("recipient", "shipment__tracking_code")
    readonly_fields = ("uuid", "created_at")
    raw_id_fields = ("shipment",)
