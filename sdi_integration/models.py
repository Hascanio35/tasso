from django.db import models

from core.models import TenantAwareModel
from sdi_integration.crypto import cifra, decifra


class ConfigurazioneSDI(TenantAwareModel):
    """Configurazione del provider SDI per una singola azienda cliente.
    Una riga per azienda: ogni cliente puo' usare un provider diverso
    (Aruba, OpenAPI.it, Fatture in Cloud...) con le proprie credenziali.

    I campi generici (api_key, client_id/secret, username/password)
    coprono gli schemi di autenticazione piu' comuni tra i provider SDI
    italiani; non tutti i provider li usano tutti — si compilano solo
    quelli richiesti dal provider scelto (vedi sdi_integration/provider.py
    per l'adapter che li consuma).
    """

    PROVIDER_CHOICES = [
        ("ARUBA", "Aruba Fatturazione Elettronica"),
        ("OPENAPI", "OpenAPI.it"),
        ("FATTURE_IN_CLOUD", "Fatture in Cloud"),
        ("ALTRO", "Altro provider / integrazione personalizzata"),
    ]

    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    api_base_url = models.URLField(
        blank=True, help_text="Endpoint API del provider, se diverso da quello di default per il provider scelto"
    )

    # tutte le credenziali sono salvate cifrate (vedi crypto.py); le
    # proprieta' sotto espongono un'interfaccia in chiaro comoda da
    # usare nel resto del codice (es. nell'adapter che chiama l'API)
    api_key_cifrata = models.TextField(blank=True)
    client_id_cifrato = models.TextField(blank=True)
    client_secret_cifrato = models.TextField(blank=True)
    username_cifrato = models.TextField(blank=True)
    password_cifrata = models.TextField(blank=True)

    attivo = models.BooleanField(default=True)
    note = models.TextField(blank=True, help_text="Es. numero di contratto, referente del provider, promemoria vari")
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configurazione SDI"
        verbose_name_plural = "Configurazioni SDI"
        constraints = [
            models.UniqueConstraint(fields=["tenant"], name="unique_configurazione_sdi_per_tenant")
        ]

    def __str__(self):
        return f"{self.get_provider_display()} ({self.tenant})"

    @property
    def api_key(self):
        return decifra(self.api_key_cifrata)

    @api_key.setter
    def api_key(self, valore):
        self.api_key_cifrata = cifra(valore)

    @property
    def client_id(self):
        return decifra(self.client_id_cifrato)

    @client_id.setter
    def client_id(self, valore):
        self.client_id_cifrato = cifra(valore)

    @property
    def client_secret(self):
        return decifra(self.client_secret_cifrato)

    @client_secret.setter
    def client_secret(self, valore):
        self.client_secret_cifrato = cifra(valore)

    @property
    def username_provider(self):
        return decifra(self.username_cifrato)

    @username_provider.setter
    def username_provider(self, valore):
        self.username_cifrato = cifra(valore)

    @property
    def password_provider(self):
        return decifra(self.password_cifrata)

    @password_provider.setter
    def password_provider(self, valore):
        self.password_cifrata = cifra(valore)
