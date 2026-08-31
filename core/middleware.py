from core.tenant_context import set_current_tenant, clear_current_tenant


class TenantMiddleware:
    """Risolve il tenant corrente per ogni request e lo salva nel contextvar.

    Strategia di risoluzione (in ordine di priorita'):
      1. utente autenticato -> request.user.tenant
      2. header X-Tenant-Id (utile per integrazioni/API server-to-server)
    Il super-admin di piattaforma (is_platform_admin=True) non ha un tenant
    fisso: puo' impersonare un tenant passando l'header esplicitamente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = None

        if request.user.is_authenticated and getattr(request.user, "tenant_id", None):
            tenant_id = request.user.tenant_id
        elif "X-Tenant-Id" in request.headers:
            tenant_id = request.headers["X-Tenant-Id"]

        if tenant_id:
            set_current_tenant(tenant_id)
        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()
        return response
