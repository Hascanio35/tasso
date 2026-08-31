from django.contrib import admin
from core.admin_mixins import TenantAwareAdminMixin
from warehouse.models import Magazzino, Giacenza, MovimentoMagazzino


@admin.register(Magazzino)
class MagazzinoAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "predefinito", "attivo")


@admin.register(Giacenza)
class GiacenzaAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("articolo", "magazzino", "quantita", "aggiornato_il")
    list_filter = ("magazzino",)
    search_fields = ("articolo__codice", "articolo__descrizione")


@admin.register(MovimentoMagazzino)
class MovimentoMagazzinoAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("data", "causale", "articolo", "magazzino", "quantita", "documento_riferimento")
    list_filter = ("causale", "magazzino")
    search_fields = ("articolo__codice", "documento_riferimento")
