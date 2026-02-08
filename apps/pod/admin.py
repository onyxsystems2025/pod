from django.contrib import admin

from .models import PODPhoto, PODRecord


class PODPhotoInline(admin.TabularInline):
    model = PODPhoto
    extra = 0
    readonly_fields = ("uuid",)


@admin.register(PODRecord)
class PODRecordAdmin(admin.ModelAdmin):
    list_display = (
        "shipment", "delivery_result", "recipient_signer_name",
        "recorded_at", "synced_from_offline",
    )
    list_filter = ("delivery_result", "synced_from_offline")
    search_fields = ("shipment__tracking_code", "recipient_signer_name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [PODPhotoInline]
    raw_id_fields = ("shipment", "driver")
