from django.contrib import admin

from .models import Shipment, ShipmentEvent


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0
    readonly_fields = ("uuid", "status", "description", "location", "recorded_by", "created_at")
    ordering = ("-created_at",)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_code", "recipient_name", "sender", "status",
        "delivery_type", "priority", "created_at",
    )
    list_filter = ("status", "delivery_type", "priority")
    search_fields = ("tracking_code", "reference", "recipient_name", "sender__company_name")
    readonly_fields = ("uuid", "tracking_code", "public_tracking_token", "created_at", "updated_at")
    inlines = [ShipmentEventInline]
    raw_id_fields = ("sender", "driver", "external_carrier", "created_by")
    date_hierarchy = "created_at"
