from django.contrib import admin, messages
from ddt.models import DocumentoTrasporto, RigaDDT


class RigaDDTInline(admin.TabularInline):
    model = RigaDDT
    extra = 1


@admin.action(description="Conferma i DDT selezionati (assegna numero e scarica il magazzino)")
def conferma_ddt(modeladmin, request, queryset):
    confermati = 0
    for ddt in queryset:
        if ddt.confermato:
            continue
        avvisi_scorta = ddt.conferma()
        confermati += 1
        for articolo in avvisi_scorta:
            messages.warning(request, f"Attenzione: '{articolo}' e' sceso sotto la scorta minima dopo il DDT {ddt.numero}/{ddt.anno}.")
    if confermati:
        messages.success(request, f"{confermati} DDT confermati: numero assegnato e magazzino scaricato.")
    else:
        messages.info(request, "Nessun DDT da confermare (erano gia' tutti confermati).")


@admin.register(DocumentoTrasporto)
class DocumentoTrasportoAdmin(admin.ModelAdmin):
    list_display = ("numero", "anno", "data_documento", "cliente", "causale_trasporto", "confermato", "fatturato")
    list_filter = ("causale_trasporto", "confermato", "fatturato")
    search_fields = ("numero", "cliente__ragione_sociale")
    inlines = [RigaDDTInline]
    actions = [conferma_ddt]

    def get_readonly_fields(self, request, obj=None):
        # una volta confermato, il DDT non e' piu' modificabile
        # (il magazzino e' gia' stato scaricato di conseguenza)
        if obj and obj.confermato:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
