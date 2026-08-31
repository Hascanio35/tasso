from django.contrib import admin, messages
from core.admin_mixins import TenantAwareAdminMixin
from documents.models import DocumentoNonFiscale, RigaDocumentoNonFiscale


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
class DocumentoNonFiscaleAdmin(TenantAwareAdminMixin, admin.ModelAdmin):
    list_display = ("tipo", "numero", "anno", "data_documento", "cliente", "stato")
    list_filter = ("tipo", "stato")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaDocumentoNonFiscaleInline]
    actions = [conferma_documenti]
