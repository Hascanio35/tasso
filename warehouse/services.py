"""
Unico punto di scrittura per la movimentazione di magazzino. Nessun altro
modulo deve modificare warehouse.Giacenza direttamente: si passa sempre
da qui, cosi' ogni variazione lascia traccia in MovimentoMagazzino ed
e' sempre coerente con la giacenza denormalizzata.
"""
from decimal import Decimal

from django.db import transaction

from warehouse.models import Giacenza, MovimentoMagazzino


def movimenta(*, tenant_id, magazzino, articolo, quantita: Decimal, causale: str, documento_riferimento: str = "", note: str = ""):
    """Registra un movimento di magazzino e aggiorna la giacenza.

    `quantita` positiva per i carichi, negativa per gli scarichi (stessa
    convenzione di MovimentoMagazzino.quantita).

    Ritorna la Giacenza aggiornata. Se dopo il movimento la quantita'
    scende sotto la scorta minima dell'articolo, lo segnala nel valore
    di ritorno (sotto_scorta_minima) cosi' il chiamante puo' avvisare
    l'utente, senza pero' bloccare l'operazione (una vendita non va
    impedita solo perche' finisce la scorta).
    """
    with transaction.atomic():
        giacenza, _ = Giacenza.objects.select_for_update().get_or_create(
            tenant_id=tenant_id, magazzino=magazzino, articolo=articolo,
        )
        MovimentoMagazzino.objects.create(
            tenant_id=tenant_id,
            magazzino=magazzino,
            articolo=articolo,
            causale=causale,
            quantita=quantita,
            documento_riferimento=documento_riferimento,
            note=note,
        )
        giacenza.quantita = giacenza.quantita + quantita
        giacenza.save(update_fields=["quantita", "aggiornato_il"])

    sotto_scorta_minima = (
        articolo.tipo == "BENE" and articolo.scorta_minima > 0 and giacenza.quantita < articolo.scorta_minima
    )
    return giacenza, sotto_scorta_minima
