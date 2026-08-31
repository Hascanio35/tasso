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

    numero = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Lasciare vuoto in bozza: viene assegnato automaticamente alla conferma",
    )
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
    confermato = models.BooleanField(
        default=False,
        help_text="True dopo l'emissione: numero assegnato e magazzino scaricato. Una bozza (False) puo' essere modificata liberamente, un DDT confermato no.",
    )
    note = models.TextField(blank=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento di trasporto (DDT)"
        verbose_name_plural = "Documenti di trasporto (DDT)"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "anno", "numero"],
                condition=models.Q(numero__isnull=False),
                name="unique_numero_ddt_per_tenant_anno",
            )
        ]
        ordering = ["-anno", "-numero"]

    def __str__(self):
        numero = self.numero if self.numero else "bozza"
        return f"DDT {numero}/{self.anno} - {self.cliente}"

    def conferma(self):
        """Assegna il numero progressivo e scarica il magazzino per ogni
        riga, in un'unica transazione. Idempotente: se il DDT e' gia'
        confermato non fa nulla (evita doppio scarico se richiamato
        due volte, es. da un doppio click sull'azione admin).

        Ritorna la lista degli articoli scesi sotto la scorta minima,
        per poter avvisare l'utente senza bloccare l'operazione.
        """
        from django.db import transaction
        from core.numbering import prossimo_numero
        from warehouse.services import movimenta

        if self.confermato:
            return []

        avvisi_scorta = []
        with transaction.atomic():
            if not self.numero:
                self.numero = prossimo_numero(self.tenant_id, "DDT", self.anno)
            documento_rif = f"DDT {self.numero}/{self.anno}"
            for riga in self.righe.select_related("articolo"):
                if riga.articolo.tipo != "BENE":
                    continue  # i servizi non movimentano magazzino
                _, sotto_scorta = movimenta(
                    tenant_id=self.tenant_id,
                    magazzino=self.magazzino_partenza,
                    articolo=riga.articolo,
                    quantita=-riga.quantita,
                    causale="SCARICO_VENDITA",
                    documento_riferimento=documento_rif,
                )
                if sotto_scorta:
                    avvisi_scorta.append(riga.articolo)
            self.confermato = True
            self.save(update_fields=["numero", "confermato"])
        return avvisi_scorta


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
