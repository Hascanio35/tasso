from django.contrib import admin

from core.admin_mixins import SoloPlatformAdmin
from sdi_integration.forms import ConfigurazioneSDIForm
from sdi_integration.models import ConfigurazioneSDI


@admin.register(ConfigurazioneSDI)
class ConfigurazioneSDIAdmin(SoloPlatformAdmin, admin.ModelAdmin):
    form = ConfigurazioneSDIForm
    list_display = ("tenant", "provider", "attivo", "aggiornato_il")
    list_filter = ("provider", "attivo")
