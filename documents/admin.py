from django.contrib import admin, messages
from core.admin_mixins import TenantAwareAdminMixin, PdfDownloadAdminMixin
from documents.models import DocumentoNonFiscale, RigaDocumentoNonFiscale
from documents.pdf import genera_pdf_documento


class RigaDocumentoNonFiscaleInline(TenantAwareAdminMixin, admin.TabularInline):
    model = RigaDocumentoNonFiscale
    extra = 1


@admin.action(description="Conferma i documenti selezionati (assegna il numero progressivo)")
def conferma_documenti(modeladmin, request, queryset):
    confermati = 0
    for documento in queryset:
        if documento.numero:
            continue
        documento.conferma()
        confermati += 1
    if confermati:
        messages.success(request, f"{confermati} documenti confermati: numero assegnato.")
    else:
        messages.info(request, "Nessun documento da confermare (avevano gia' un numero).")


@admin.register(DocumentoNonFiscale)
class DocumentoNonFiscaleAdmin(TenantAwareAdminMixin, PdfDownloadAdminMixin, admin.ModelAdmin):
    funzione_genera_pdf = staticmethod(genera_pdf_documento)
    campo_stato_confermato = None  # il PDF e' disponibile anche in bozza (utile per preventivi da rivedere)

    list_display = ("tipo", "numero", "anno", "data_documento", "cliente", "stato", "link_pdf")
    list_filter = ("tipo", "stato")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaDocumentoNonFiscaleInline]
    actions = [conferma_documenti]
    readonly_fields = ["link_pdf"]
