from django.db import models

from core.models import TenantAwareModel
from clients.models import Anagrafica
from catalog.models import Articolo


class DocumentoNonFiscale(TenantAwareModel):
    """Documenti che non hanno rilevanza fiscale/SDI: preventivi, ordini
    cliente/fornitore, ricevute di cortesia, rapportini di intervento, ecc.
    Volutamente generico e riusabile per piu' tipologie, distinte da `tipo`.
    """

    TIPO = [
        ("PREVENTIVO", "Preventivo"),
        ("ORDINE_CLIENTE", "Ordine cliente"),
        ("ORDINE_FORNITORE", "Ordine fornitore"),
        ("RICEVUTA", "Ricevuta di cortesia"),
        ("RAPPORTINO", "Rapportino di intervento"),
    ]
    STATO = [
        ("BOZZA", "Bozza"),
        ("INVIATO", "Inviato al destinatario"),
        ("ACCETTATO", "Accettato/confermato"),
        ("RIFIUTATO", "Rifiutato"),
        ("CHIUSO", "Chiuso"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO)
    numero = models.PositiveIntegerField()
    anno = models.PositiveIntegerField()
    data_documento = models.DateField()
    cliente = models.ForeignKey(
        Anagrafica, null=True, blank=True, on_delete=models.PROTECT, related_name="documenti_non_fiscali"
    )
    stato = models.CharField(max_length=20, choices=STATO, default="BOZZA")
    validita_giorni = models.PositiveIntegerField(null=True, blank=True, help_text="Per i preventivi")
    imponibile = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento non fiscale"
        verbose_name_plural = "Documenti non fiscali"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "tipo", "anno", "numero"], name="unique_numero_doc_per_tenant_tipo_anno"
            )
        ]
        ordering = ["-anno", "-numero"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.numero}/{self.anno} - {self.cliente or ''}"


class RigaDocumentoNonFiscale(TenantAwareModel):
    documento = models.ForeignKey(DocumentoNonFiscale, on_delete=models.CASCADE, related_name="righe")
    numero_riga = models.PositiveIntegerField()
    articolo = models.ForeignKey(Articolo, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    descrizione = models.CharField(max_length=255)
    quantita = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    prezzo_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    class Meta:
        verbose_name = "Riga documento"
        verbose_name_plural = "Righe documento"
        ordering = ["numero_riga"]
        constraints = [
            models.UniqueConstraint(fields=["documento", "numero_riga"], name="unique_numero_riga_per_documento")
        ]

    def __str__(self):
        return f"Riga {self.numero_riga} - {self.descrizione}"
