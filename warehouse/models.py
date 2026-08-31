from django.db import models

from core.models import TenantAwareModel
from catalog.models import Articolo


class Magazzino(TenantAwareModel):
    """Un deposito fisico o logico (es. 'Sede', 'Furgone tecnico 1')."""

    nome = models.CharField(max_length=100)
    indirizzo = models.CharField(max_length=255, blank=True)
    predefinito = models.BooleanField(default=False)
    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Magazzino"
        verbose_name_plural = "Magazzini"

    def __str__(self):
        return self.nome


class Giacenza(TenantAwareModel):
    """Quantita' corrente di un articolo in un magazzino.
    Denormalizzata per letture veloci; la fonte di verita' resta comunque
    la somma dei MovimentoMagazzino, ricalcolabile in caso di disallineamento.
    """

    magazzino = models.ForeignKey(Magazzino, on_delete=models.CASCADE, related_name="giacenze")
    articolo = models.ForeignKey(Articolo, on_delete=models.CASCADE, related_name="giacenze")
    quantita = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    aggiornato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giacenza"
        verbose_name_plural = "Giacenze"
        constraints = [
            models.UniqueConstraint(fields=["magazzino", "articolo"], name="unique_giacenza_magazzino_articolo")
        ]

    def __str__(self):
        return f"{self.articolo} @ {self.magazzino}: {self.quantita}"


class MovimentoMagazzino(TenantAwareModel):
    """Ogni entrata/uscita di magazzino. E' l'unica scrittura ammessa:
    la Giacenza viene sempre aggiornata a partire da qui (in una
    transazione), mai modificata direttamente."""

    CAUSALE = [
        ("CARICO_ACQUISTO", "Carico da acquisto"),
        ("CARICO_RESO_CLIENTE", "Carico da reso cliente"),
        ("CARICO_RETTIFICA", "Rettifica di inventario (carico)"),
        ("SCARICO_VENDITA", "Scarico per vendita/DDT"),
        ("SCARICO_RESO_FORNITORE", "Scarico per reso a fornitore"),
        ("SCARICO_RETTIFICA", "Rettifica di inventario (scarico)"),
        ("TRASFERIMENTO", "Trasferimento tra magazzini"),
    ]

    magazzino = models.ForeignKey(Magazzino, on_delete=models.PROTECT, related_name="movimenti")
    articolo = models.ForeignKey(Articolo, on_delete=models.PROTECT, related_name="movimenti")
    causale = models.CharField(max_length=30, choices=CAUSALE)
    quantita = models.DecimalField(
        max_digits=14, decimal_places=3,
        help_text="Positiva per i carichi, negativa per gli scarichi",
    )
    data = models.DateTimeField(auto_now_add=True)
    # riferimento generico al documento che ha generato il movimento
    # (DDT, fattura, rettifica manuale...) tramite content type, per non
    # accoppiare rigidamente questa app a invoicing/ddt
    documento_riferimento = models.CharField(
        max_length=100, blank=True,
        help_text="es. 'DDT 2026/145' o 'Fattura 2026/302', per tracciabilita' rapida",
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Movimento di magazzino"
        verbose_name_plural = "Movimenti di magazzino"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_causale_display()} {self.quantita} {self.articolo} ({self.magazzino})"
