from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from core.models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("ragione_sociale", "partita_iva", "citta", "attivo")
    search_fields = ("ragione_sociale", "partita_iva")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "tenant", "is_platform_admin", "is_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Tenant", {"fields": ("tenant", "is_platform_admin")}),
    )
