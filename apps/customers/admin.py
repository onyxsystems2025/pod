from django.contrib import admin

from .models import Address, Customer


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("company_name", "contact_name", "email", "phone", "customer_type", "is_active")
    list_filter = ("customer_type", "is_active")
    search_fields = ("company_name", "contact_name", "email")
    inlines = [AddressInline]
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "label", "street", "city", "province", "postal_code")
    list_filter = ("province",)
    search_fields = ("street", "city", "customer__company_name")
    readonly_fields = ("uuid",)
