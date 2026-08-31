from django.contrib import admin
from core.admin_mixins import TenantAwareAdminMixin
from catalog.models import Articolo, CategoriaArticolo


@admin.register(CategoriaArticolo)
class CategoriaArticoloAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "categoria_padre")


@admin.register(Articolo)
class ArticoloAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("codice", "descrizione", "tipo", "prezzo_vendita", "aliquota_iva", "attivo")
    search_fields = ("codice", "descrizione")
    list_filter = ("tipo", "attivo")
