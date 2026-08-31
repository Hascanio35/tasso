from django.contrib import admin
from ddt.models import DocumentoTrasporto, RigaDDT


class RigaDDTInline(admin.TabularInline):
    model = RigaDDT
    extra = 1


@admin.register(DocumentoTrasporto)
class DocumentoTrasportoAdmin(admin.ModelAdmin):
    list_display = ("numero", "anno", "data_documento", "cliente", "causale_trasporto", "fatturato")
    list_filter = ("causale_trasporto", "fatturato")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaDDTInline]
