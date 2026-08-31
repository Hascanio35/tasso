"""
Numerazione automatica dei documenti, sicura in concorrenza.

Ogni chiamata a `prossimo_numero` va fatta dentro una request/azione che
gia' e' (o diventa) una transazione atomica: la riga del contatore viene
bloccata con select_for_update(), cosi' due richieste simultanee non
possono mai ottenere lo stesso numero.
"""
from django.db import transaction

from core.models import Contatore


def prossimo_numero(tenant_id, chiave: str, anno: int) -> int:
    """Ritorna il prossimo numero progressivo per (tenant, chiave, anno),
    creando il contatore se non esiste ancora. Deve essere chiamata
    dentro una transaction.atomic() (i modelli che la usano lo fanno
    gia' internamente nei loro metodi conferma()/emetti()).
    """
    with transaction.atomic():
        contatore, _ = Contatore.objects.select_for_update().get_or_create(
            tenant_id=tenant_id, chiave=chiave, anno=anno,
        )
        contatore.ultimo_numero += 1
        contatore.save(update_fields=["ultimo_numero"])
        return contatore.ultimo_numero
