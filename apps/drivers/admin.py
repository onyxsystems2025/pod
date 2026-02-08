from django.contrib import admin

from .models import Driver, ExternalCarrier


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_plate", "vehicle_type", "zone", "status", "is_active")
    list_filter = ("status", "is_active", "zone")
    search_fields = ("user__first_name", "user__last_name", "vehicle_plate")
    readonly_fields = ("uuid",)


@admin.register(ExternalCarrier)
class ExternalCarrierAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("uuid",)
