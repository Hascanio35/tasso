from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from core.admin_mixins import SoloPlatformAdmin
from core.models import Tenant, User, Contatore

admin.site.site_header = "Tasso — Gestionale multi-azienda"
admin.site.site_title = "Tasso"
admin.site.index_title = "Pannello di amministrazione"


@admin.register(Tenant)
class TenantAdmin(SoloPlatformAdmin, admin.ModelAdmin):
    list_display = ("ragione_sociale", "partita_iva", "citta", "attivo")
    search_fields = ("ragione_sociale", "partita_iva")


@admin.register(User)
class UserAdmin(SoloPlatformAdmin, DjangoUserAdmin):
    list_display = ("username", "email", "tenant", "is_platform_admin", "is_staff", "is_active")
    list_filter = DjangoUserAdmin.list_filter + ("tenant",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Tenant", {"fields": ("tenant", "is_platform_admin")}),
    )


@admin.register(Contatore)
class ContatoreAdmin(SoloPlatformAdmin, admin.ModelAdmin):
    list_display = ("chiave", "anno", "ultimo_numero", "tenant")
    list_filter = ("chiave", "anno")
