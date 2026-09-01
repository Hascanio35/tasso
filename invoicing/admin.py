from django.contrib import admin, messages
from core.admin_mixins import TenantAwareAdminMixin, PdfDownloadAdminMixin
from invoicing.models import Fattura, RigaFattura, SerieNumerazione
from invoicing.pdf import genera_pdf_fattura


class RigaFatturaInline(TenantAwareAdminMixin, admin.TabularInline):
    model = RigaFattura
    extra = 1

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.confermata:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.confermata:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.confermata:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(SerieNumerazione)
class SerieNumerazioneAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("codice", "anno", "ultimo_numero")


@admin.action(description="Emetti le fatture selezionate (assegna numero, XML FatturaPA e scarica il magazzino se immediate)")
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
        messages.success(request, f"{emesse} fatture emesse: numero assegnato, XML FatturaPA generato, magazzino scaricato dove necessario.")
    else:
        messages.info(request, "Nessuna fattura emessa (gia' confermate o bloccate per magazzino mancante).")


@admin.action(description="Rigenera l'XML FatturaPA per le fatture selezionate (gia' emesse)")
def rigenera_xml(modeladmin, request, queryset):
    aggiornate = 0
    for fattura in queryset.filter(confermata=True):
        fattura.rigenera_xml()
        aggiornate += 1
    if aggiornate:
        messages.success(request, f"XML FatturaPA rigenerato per {aggiornate} fatture.")
    else:
        messages.info(request, "Nessuna fattura emessa tra quelle selezionate.")


@admin.action(description="Invia a SDI le fatture selezionate (gia' emesse)")
def invia_a_sdi(modeladmin, request, queryset):
    from sdi_integration.services import invia_fattura_a_sdi
    inviate = 0
    for fattura in queryset.filter(confermata=True):
        if fattura.stato_sdi not in ("BOZZA", "DA_INVIARE", "SCARTATA", "MANCATA_CONSEGNA"):
            continue
        try:
            invia_fattura_a_sdi(fattura)
            inviate += 1
        except Exception as errore:
            messages.error(request, f"Errore inviando {fattura}: {errore}")
    if inviate:
        messages.success(request, f"{inviate} fatture inviate a SDI.")
    else:
        messages.info(request, "Nessuna fattura inviata (gia' inviate, non emesse, o errori — vedi sopra).")


@admin.action(description="Aggiorna lo stato SDI delle fatture selezionate")
def aggiorna_stato_sdi(modeladmin, request, queryset):
    from sdi_integration.services import aggiorna_stato_fattura
    aggiornate = 0
    for fattura in queryset.exclude(identificativo_sdi=""):
        try:
            aggiorna_stato_fattura(fattura)
            aggiornate += 1
        except Exception as errore:
            messages.error(request, f"Errore aggiornando {fattura}: {errore}")
    if aggiornate:
        messages.success(request, f"Stato SDI aggiornato per {aggiornate} fatture.")
    else:
        messages.info(request, "Nessuna fattura da aggiornare (nessuna ha ancora un identificativo SDI).")


@admin.register(Fattura)
class FatturaAdmin(TenantAwareAdminMixin, PdfDownloadAdminMixin, admin.ModelAdmin):
    funzione_genera_pdf = staticmethod(genera_pdf_fattura)
    campo_stato_confermato = "confermata"

    list_display = ("numero", "serie", "data_documento", "cliente", "totale", "confermata", "stato_sdi", "link_pdf")
    list_filter = ("stato_sdi", "tipo_documento_sdi", "serie", "confermata")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaFatturaInline]
    actions = [emetti_fatture, rigenera_xml, invia_a_sdi, aggiorna_stato_sdi]

    def get_readonly_fields(self, request, obj=None):
        base = ["link_pdf"]
        if obj and obj.confermata:
            return base + [f.name for f in self.model._meta.fields]
        return base + list(super().get_readonly_fields(request, obj))
