from django.db import models

from core.models import TenantAwareModel
from clients.models import Anagrafica, IndirizzoSpedizione
from catalog.models import Articolo
from warehouse.models import Magazzino


class DocumentoTrasporto(TenantAwareModel):
    CAUSALE_TRASPORTO = [
        ("VENDITA", "Vendita"),
        ("CONTO_VISIONE", "Conto visione/prova"),
        ("CONTO_LAVORAZIONE", "Conto lavorazione"),
        ("RESO", "Reso"),
        ("TRASFERIMENTO", "Trasferimento tra sedi"),
        ("RIPARAZIONE", "Riparazione/assistenza tecnica"),
    ]
    ASPETTO_BENI = [
        ("COLLI", "A colli"),
        ("SFUSO", "Sfuso"),
        ("PALLET", "Pallet"),
    ]
    PORTO = [("FRANCO", "Franco (mittente)"), ("ASSEGNATO", "Assegnato (destinatario)")]

    numero = models.PositiveIntegerField()
    anno = models.PositiveIntegerField()
    data_documento = models.DateField()
    ora_inizio_trasporto = models.TimeField(null=True, blank=True)

    cliente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name="ddt")
    indirizzo_destinazione = models.ForeignKey(
        IndirizzoSpedizione, null=True, blank=True, on_delete=models.SET_NULL, related_name="ddt"
    )
    magazzino_partenza = models.ForeignKey(Magazzino, on_delete=models.PROTECT, related_name="ddt_partenza")

    causale_trasporto = models.CharField(max_length=20, choices=CAUSALE_TRASPORTO, default="VENDITA")
    aspetto_beni = models.CharField(max_length=10, choices=ASPETTO_BENI, default="COLLI")
    numero_colli = models.PositiveIntegerField(null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    porto = models.CharField(max_length=10, choices=PORTO, default="FRANCO")
    vettore = models.CharField(max_length=255, blank=True)

    fatturato = models.BooleanField(default=False, help_text="True quando confluito in una fattura differita")
    note = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento di trasporto (DDT)"
        verbose_name_plural = "Documenti di trasporto (DDT)"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "anno", "numero"], name="unique_numero_ddt_per_tenant_anno")
        ]
        ordering = ["-anno", "-numero"]

    def __str__(self):
        return f"DDT {self.numero}/{self.anno} - {self.cliente}"


class RigaDDT(TenantAwareModel):
    ddt = models.ForeignKey(DocumentoTrasporto, on_delete=models.CASCADE, related_name="righe")
    numero_riga = models.PositiveIntegerField()
    articolo = models.ForeignKey(Articolo, on_delete=models.PROTECT, related_name="+")
    descrizione = models.CharField(max_length=255, blank=True, help_text="Se vuota, si usa la descrizione dell'articolo")
    quantita = models.DecimalField(max_digits=14, decimal_places=3)

    class Meta:
        verbose_name = "Riga DDT"
        verbose_name_plural = "Righe DDT"
        ordering = ["numero_riga"]
        constraints = [
            models.UniqueConstraint(fields=["ddt", "numero_riga"], name="unique_numero_riga_per_ddt")
        ]

    def __str__(self):
        return f"Riga {self.numero_riga} - {self.articolo}"
