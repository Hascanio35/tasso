import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.tenant_context import get_current_tenant_id


class Tenant(models.Model):
    """Un'azienda cliente del gestionale (multi-tenant)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ragione_sociale = models.CharField(max_length=255)
    partita_iva = models.CharField(max_length=11)
    codice_fiscale = models.CharField(max_length=16, blank=True)
    codice_destinatario_sdi = models.CharField(
        max_length=7, blank=True,
        help_text="Codice destinatario a 7 cifre per la ricezione fatture attive via SDI (o 0000000 se PEC)",
    )
    pec = models.EmailField(blank=True)
    indirizzo = models.CharField(max_length=255, blank=True)
    cap = models.CharField(max_length=10, blank=True)
    citta = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=2, blank=True)
    attivo = models.BooleanField(default=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    # necessari per generare l'XML FatturaPA (vedi invoicing/fatturapa.py)
    regime_fiscale = models.CharField(
        max_length=4, default="RF01",
        help_text="Codice regime fiscale per la fattura elettronica. Il piu' comune e' RF01 (ordinario); "
                   "RF19 e' il regime forfettario. Altri codici: consulta il tuo commercialista se necessario.",
    )
    iban = models.CharField(max_length=34, blank=True, help_text="Mostrato come modalita' di pagamento in fatture e XML")
    giorni_attesa_invio_sdi = models.PositiveIntegerField(
        default=3,
        help_text="Giorni di attesa dopo l'emissione di una fattura prima dell'invio automatico a SDI. "
                   "0 = nessuna attesa (il task schedulato la invia al primo giro utile). "
                   "L'azione manuale 'Invia a SDI' resta comunque disponibile per inviare subito.",
    )

    # branding dei documenti PDF (fatture/DDT/documenti) — impostabile
    # solo qui, dal platform admin: nessun utente cliente puo' toccarlo
    logo = models.ImageField(upload_to="loghi_aziende/", blank=True, null=True)
    colore_accento = models.CharField(
        max_length=7, default="#1f1a17", help_text="Colore in formato esadecimale, es. #1f1a17, usato nell'intestazione dei documenti PDF"
    )
    piede_pagina_legale = models.TextField(
        blank=True,
        help_text="Testo libero stampato in fondo a fatture/DDT/documenti, es. capitale sociale, numero REA, tribunale competente",
    )

    class Meta:
        verbose_name = "Azienda (tenant)"
        verbose_name_plural = "Aziende (tenant)"

    def __str__(self):
        return self.ragione_sociale


class User(AbstractUser):
    """Utente applicativo, sempre legato a un tenant (tranne i super-admin di piattaforma)."""

    tenant = models.ForeignKey(
        Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name="utenti",
        help_text="Nullo solo per gli amministratori della piattaforma",
    )
    is_platform_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class TenantManager(models.Manager):
    """Manager di default: filtra automaticamente per il tenant corrente
    (impostato dal middleware in un contextvar per la durata della request).
    Le query di background/management command devono impostare esplicitamente
    il tenant con `core.tenant_context.set_current_tenant(tenant_id)`.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        return qs


class TenantAwareModel(models.Model):
    """Classe base per tutti i modelli di business: aggiunge il FK tenant
    e il manager che filtra automaticamente. Ogni app di dominio
    (clients, catalog, warehouse, invoicing, ddt, documents) eredita da qui.
    """

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="+")

    objects = TenantManager()
    all_objects = models.Manager()  # accesso non filtrato, solo per admin/migrazioni

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.tenant_id is None:
            self.tenant_id = get_current_tenant_id()
        super().save(*args, **kwargs)


class Contatore(models.Model):
    """Contatore generico per assegnare numeri progressivi a un qualunque
    tipo di documento (DDT, documenti non fiscali per tipo, ecc), un
    contatore per tenant+chiave+anno. Le fatture usano invece
    invoicing.SerieNumerazione (gia' modellata con lo stesso principio),
    per poter avere piu' serie configurabili dall'utente.

    L'incremento va sempre fatto dentro una transazione con
    select_for_update() sulla riga (vedi core.numbering.prossimo_numero),
    per evitare numeri duplicati in caso di richieste concorrenti.
    """

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="+")
    chiave = models.CharField(max_length=50, help_text="es. 'DDT', 'PREVENTIVO', 'ORDINE_CLIENTE'")
    anno = models.PositiveIntegerField()
    ultimo_numero = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Contatore di numerazione"
        verbose_name_plural = "Contatori di numerazione"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "chiave", "anno"], name="unique_contatore_per_tenant_chiave_anno")
        ]

    def __str__(self):
        return f"{self.chiave}/{self.anno} (tenant {self.tenant_id}): {self.ultimo_numero}"
