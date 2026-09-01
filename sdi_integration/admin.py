from django.contrib import admin, messages

from core.admin_mixins import SoloPlatformAdmin
from sdi_integration.forms import ConfigurazioneSDIForm
from sdi_integration.models import ConfigurazioneSDI
from sdi_integration.provider import ottieni_provider


@admin.action(description="Registra l'azienda presso il provider (una tantum, prima del primo invio)")
def registra_azienda_provider(modeladmin, request, queryset):
    registrate = 0
    for configurazione in queryset:
        try:
            provider = ottieni_provider(configurazione)
        except NotImplementedError as errore:
            messages.error(request, str(errore))
            continue
        if not hasattr(provider, "crea_configurazione_azienda"):
            messages.warning(request, f"Il provider di {configurazione} non richiede/non supporta la registrazione automatica.")
            continue
        if not configurazione.tenant.pec:
            messages.error(request, f"{configurazione.tenant}: imposta prima una PEC nell'anagrafica azienda (serve come email di riferimento per il provider).")
            continue
        try:
            provider.crea_configurazione_azienda(configurazione, configurazione.tenant, configurazione.tenant.pec)
            registrate += 1
        except Exception as errore:
            messages.error(request, f"Errore registrando {configurazione}: {errore}")
    if registrate:
        messages.success(request, f"{registrate} aziende registrate presso il provider.")


@admin.register(ConfigurazioneSDI)
class ConfigurazioneSDIAdmin(SoloPlatformAdmin, admin.ModelAdmin):
    form = ConfigurazioneSDIForm
    list_display = ("tenant", "provider", "attivo", "aggiornato_il")
    list_filter = ("provider", "attivo")
    actions = [registra_azienda_provider]
