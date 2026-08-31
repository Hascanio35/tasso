from django.contrib import admin
from clients.models import Anagrafica, IndirizzoSpedizione


class IndirizzoSpedizioneInline(admin.TabularInline):
    model = IndirizzoSpedizione
    extra = 0


@admin.register(Anagrafica)
class AnagraficaAdmin(admin.ModelAdmin):
    list_display = ("ragione_sociale", "partita_iva", "is_cliente", "is_fornitore", "citta", "attivo")
    search_fields = ("ragione_sociale", "partita_iva", "codice_fiscale")
    list_filter = ("is_cliente", "is_fornitore", "attivo")
    inlines = [IndirizzoSpedizioneInline]
