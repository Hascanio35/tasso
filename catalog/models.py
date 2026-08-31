from django.db import models

from core.models import TenantAwareModel


class CategoriaArticolo(TenantAwareModel):
    nome = models.CharField(max_length=100)
    categoria_padre = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="sottocategorie"
    )

    class Meta:
        verbose_name = "Categoria articolo"
        verbose_name_plural = "Categorie articolo"

    def __str__(self):
        return self.nome


class Articolo(TenantAwareModel):
    TIPO = [
        ("BENE", "Bene fisico (gestito a magazzino)"),
        ("SERVIZIO", "Servizio (non gestito a magazzino)"),
    ]

    codice = models.CharField(max_length=50)
    descrizione = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO, default="BENE")
    categoria = models.ForeignKey(
        CategoriaArticolo, null=True, blank=True, on_delete=models.SET_NULL, related_name="articoli"
    )
    unita_misura = models.CharField(max_length=10, default="PZ")
    prezzo_vendita = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    aliquota_iva = models.DecimalField(
        max_digits=5, decimal_places=2, default=22,
        help_text="Percentuale IVA applicata (es. 22.00, 10.00, 4.00, 0.00)",
    )
    natura_iva = models.CharField(
        max_length=4, blank=True,
        help_text="Codice natura IVA per fattura elettronica se aliquota 0 (es. N1, N2.1, N3.5...)",
    )
    scorta_minima = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    attivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Articolo"
        verbose_name_plural = "Articoli"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "codice"], name="unique_codice_articolo_per_tenant")
        ]

    def __str__(self):
        return f"{self.codice} - {self.descrizione}"
