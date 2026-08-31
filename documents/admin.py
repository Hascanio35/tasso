from django.contrib import admin
from documents.models import DocumentoNonFiscale, RigaDocumentoNonFiscale


class RigaDocumentoNonFiscaleInline(admin.TabularInline):
    model = RigaDocumentoNonFiscale
    extra = 1


@admin.register(DocumentoNonFiscale)
class DocumentoNonFiscaleAdmin(admin.ModelAdmin):
    list_display = ("tipo", "numero", "anno", "data_documento", "cliente", "stato")
    list_filter = ("tipo", "stato")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaDocumentoNonFiscaleInline]
