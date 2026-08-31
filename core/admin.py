from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from core.models import Tenant, User, Contatore

admin.site.site_header = "Tasso — Gestionale multi-azienda"
admin.site.site_title = "Tasso"
admin.site.index_title = "Pannello di amministrazione"


class SoloPlatformAdmin:
    """Mixin per ModelAdmin: la sezione e' visibile e utilizzabile solo
    dai super-admin di piattaforma (o dai superuser Django). Un utente
    normale di un'azienda cliente non vede nemmeno la voce di menu,
    a prescindere da eventuali permessi assegnati per errore."""

    def _e_platform_admin(self, request):
        return request.user.is_superuser or getattr(request.user, "is_platform_admin", False)

    def has_module_permission(self, request):
        return self._e_platform_admin(request) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self._e_platform_admin(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self._e_platform_admin(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._e_platform_admin(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._e_platform_admin(request) and super().has_delete_permission(request, obj)


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
