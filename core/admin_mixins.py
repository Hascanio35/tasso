"""
Mixin da applicare a ogni ModelAdmin (e Inline) di un modello che eredita
da core.models.TenantAwareModel.

Fa due cose:

1. Nasconde del tutto i moduli business (clients, catalog, warehouse,
   invoicing, ddt, documents) al platform admin: chi gestisce la
   piattaforma vede solo Aziende e Utenti, mai i dati operativi delle
   aziende clienti. Questo blocco vale anche per un account superuser
   Django, che normalmente bypasserebbe qualunque controllo di permesso
   — qui il controllo avviene PRIMA della chiamata a super(), quindi
   il bypass automatico di Django non si applica.

2. Per gli utenti normali (di un'azienda cliente), nasconde il campo
   'tenant' dal form — che altrimenti esporrebbe l'elenco di TUTTE le
   aziende clienti e permetterebbe di assegnare un documento
   all'azienda sbagliata — e lo assegna automaticamente in base al
   loro utente, sia per l'oggetto principale sia per le righe inline.
"""


class TenantAwareAdminMixin:
    def _e_platform_admin(self, request):
        return getattr(request.user, "is_platform_admin", False)

    def has_module_permission(self, request):
        if self._e_platform_admin(request):
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if self._e_platform_admin(request):
            return False
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if self._e_platform_admin(request):
            return False
        try:
            return super().has_add_permission(request, obj)
        except TypeError:
            # ModelAdmin.has_add_permission (non-inline) accetta solo request
            return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._e_platform_admin(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._e_platform_admin(request):
            return False
        return super().has_delete_permission(request, obj)

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if not request.user.is_superuser and "tenant" not in exclude:
            exclude.append("tenant")
        return exclude

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.tenant_id = request.user.tenant_id
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if request.user.is_superuser:
            formset.save()
            return
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, "tenant_id"):
                instance.tenant_id = request.user.tenant_id
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()
