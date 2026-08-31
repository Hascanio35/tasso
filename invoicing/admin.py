from django.contrib import admin, messages
from invoicing.models import Fattura, RigaFattura, SerieNumerazione


class RigaFatturaInline(admin.TabularInline):
    model = RigaFattura
    extra = 1


@admin.register(SerieNumerazione)
class SerieNumerazioneAdmin(admin.ModelAdmin):
    list_display = ("codice", "anno", "ultimo_numero")


@admin.action(description="Emetti le fatture selezionate (assegna numero e scarica il magazzino se immediate)")
def emetti_fatture(modeladmin, request, queryset):
    emesse = 0
    for fattura in queryset:
        if fattura.confermata:
            continue
        if not fattura.ddt_collegati.exists() and not fattura.magazzino_id:
            righe_con_beni = fattura.righe.filter(articolo__tipo="BENE").exists()
            if righe_con_beni:
                messages.error(
                    request,
                    f"Fattura {fattura} contiene beni fisici ma non ha un magazzino di scarico impostato: emissione saltata.",
                )
                continue
        avvisi_scorta = fattura.emetti()
        emesse += 1
        for articolo in avvisi_scorta:
            messages.warning(request, f"Attenzione: '{articolo}' e' sceso sotto la scorta minima dopo la fattura {fattura}.")
    if emesse:
        messages.success(request, f"{emesse} fatture emesse: numero assegnato e magazzino scaricato dove necessario.")
    else:
        messages.info(request, "Nessuna fattura emessa (gia' confermate o bloccate per magazzino mancante).")


@admin.register(Fattura)
class FatturaAdmin(admin.ModelAdmin):
    list_display = ("numero", "serie", "data_documento", "cliente", "totale", "confermata", "stato_sdi")
    list_filter = ("stato_sdi", "tipo_documento_sdi", "serie", "confermata")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaFatturaInline]
    actions = [emetti_fatture]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.confermata:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
