from django.db import models

from core.models import TenantAwareModel
from clients.models import Anagrafica
from catalog.models import Articolo


class SerieNumerazione(TenantAwareModel):
    """Serie di numerazione fatture (spesso una per anno, o una per
    tipologia: 'FT' fatture ordinarie, 'NC' note di credito...).
    Tenere la numerazione qui evita race condition sul contatore."""

    codice = models.CharField(max_length=10, help_text="es. FT, NC")
    anno = models.PositiveIntegerField()
    ultimo_numero = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Serie di numerazione"
        verbose_name_plural = "Serie di numerazione"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "codice", "anno"], name="unique_serie_per_tenant_anno")
        ]

    def __str__(self):
        return f"{self.codice}/{self.anno}"


class Fattura(TenantAwareModel):
    TIPO_DOCUMENTO_SDI = [
        ("TD01", "TD01 - Fattura"),
        ("TD04", "TD04 - Nota di credito"),
        ("TD05", "TD05 - Nota di debito"),
        ("TD24", "TD24 - Fattura differita (art. 21 c.4 lett. a)"),
    ]
    STATO_SDI = [
        ("BOZZA", "Bozza"),
        ("DA_INVIARE", "Da inviare a SDI"),
        ("INVIATA", "Inviata, in attesa di esito"),
        ("CONSEGNATA", "Consegnata al destinatario"),
        ("SCARTATA", "Scartata da SDI"),
        ("MANCATA_CONSEGNA", "Mancata consegna (impegnativa comunque)"),
        ("NON_FISCALE", "Documento non inviato a SDI"),
    ]

    serie = models.ForeignKey(SerieNumerazione, on_delete=models.PROTECT, related_name="fatture")
    numero = models.PositiveIntegerField()
    data_documento = models.DateField()
    tipo_documento_sdi = models.CharField(max_length=4, choices=TIPO_DOCUMENTO_SDI, default="TD01")

    cliente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name="fatture")

    # riferimenti a eventuali DDT collegati (fattura differita da DDT multipli)
    ddt_collegati = models.ManyToManyField("ddt.DocumentoTrasporto", blank=True, related_name="fatture")

    imponibile = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    imposta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    totale = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    stato_sdi = models.CharField(max_length=20, choices=STATO_SDI, default="BOZZA")
    identificativo_sdi = models.CharField(max_length=50, blank=True, help_text="ID assegnato da SDI dopo l'invio")
    xml_fatturapa = models.TextField(blank=True, help_text="XML FatturaPA generato, conservato per l'invio/conservazione")
    ricevuta_sdi = models.TextField(blank=True, help_text="Ultima ricevuta/notifica ricevuta dal provider SDI")

    note = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fattura"
        verbose_name_plural = "Fatture"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "serie", "numero"], name="unique_numero_fattura_per_serie")
        ]
        ordering = ["-data_documento", "-numero"]

    def __str__(self):
        return f"{self.serie.codice} {self.numero}/{self.serie.anno} - {self.cliente}"


class RigaFattura(TenantAwareModel):
    fattura = models.ForeignKey(Fattura, on_delete=models.CASCADE, related_name="righe")
    numero_riga = models.PositiveIntegerField()
    articolo = models.ForeignKey(Articolo, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    descrizione = models.CharField(max_length=255)
    quantita = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    prezzo_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    sconto_percentuale = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aliquota_iva = models.DecimalField(max_digits=5, decimal_places=2, default=22)
    natura_iva = models.CharField(max_length=4, blank=True)

    class Meta:
        verbose_name = "Riga fattura"
        verbose_name_plural = "Righe fattura"
        ordering = ["numero_riga"]
        constraints = [
            models.UniqueConstraint(fields=["fattura", "numero_riga"], name="unique_numero_riga_per_fattura")
        ]

    @property
    def imponibile_riga(self):
        lordo = self.quantita * self.prezzo_unitario
        return lordo * (1 - self.sconto_percentuale / 100)

    def __str__(self):
        return f"Riga {self.numero_riga} - {self.descrizione}"
