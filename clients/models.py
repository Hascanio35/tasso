from django.db import models

from core.models import TenantAwareModel


class Anagrafica(TenantAwareModel):
    """Cliente e/o fornitore. Un unico modello con flag, per evitare
    duplicazione quando lo stesso soggetto e' sia cliente sia fornitore."""

    TIPO_SOGGETTO = [
        ("PF", "Persona fisica"),
        ("PG", "Persona giuridica"),
    ]

    is_cliente = models.BooleanField(default=True)
    is_fornitore = models.BooleanField(default=False)

    tipo_soggetto = models.CharField(max_length=2, choices=TIPO_SOGGETTO, default="PG")
    ragione_sociale = models.CharField(max_length=255)
    partita_iva = models.CharField(max_length=11, blank=True)
    codice_fiscale = models.CharField(max_length=16, blank=True)

    # dati necessari per la fattura elettronica (allegato al cliente)
    codice_destinatario_sdi = models.CharField(max_length=7, blank=True, default="0000000")
    pec_fatturazione = models.EmailField(blank=True)

    indirizzo = models.CharField(max_length=255, blank=True)
    cap = models.CharField(max_length=10, blank=True)
    citta = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=2, blank=True)
    nazione = models.CharField(max_length=2, default="IT")

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    note = models.TextField(blank=True)
    attivo = models.BooleanField(default=True)
    creato_il = models.DateTimeField(auto_now_add=True)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Anagrafica cliente/fornitore"
        verbose_name_plural = "Anagrafiche clienti/fornitori"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "partita_iva"],
                condition=~models.Q(partita_iva=""),
                name="unique_piva_per_tenant",
            )
        ]

    def __str__(self):
        return self.ragione_sociale


class IndirizzoSpedizione(TenantAwareModel):
    """Sedi/destinazioni multiple per uno stesso cliente, usate nei DDT."""

    anagrafica = models.ForeignKey(Anagrafica, on_delete=models.CASCADE, related_name="indirizzi_spedizione")
    descrizione = models.CharField(max_length=100, blank=True, help_text="es. 'Magazzino nord'")
    indirizzo = models.CharField(max_length=255)
    cap = models.CharField(max_length=10, blank=True)
    citta = models.CharField(max_length=100)
    provincia = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return f"{self.descrizione or self.citta} ({self.anagrafica})"
