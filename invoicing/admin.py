from django.contrib import admin
from invoicing.models import Fattura, RigaFattura, SerieNumerazione


class RigaFatturaInline(admin.TabularInline):
    model = RigaFattura
    extra = 1


@admin.register(SerieNumerazione)
class SerieNumerazioneAdmin(admin.ModelAdmin):
    list_display = ("codice", "anno", "ultimo_numero")


@admin.register(Fattura)
class FatturaAdmin(admin.ModelAdmin):
    list_display = ("numero", "serie", "data_documento", "cliente", "totale", "stato_sdi")
    list_filter = ("stato_sdi", "tipo_documento_sdi", "serie")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaFatturaInline]
