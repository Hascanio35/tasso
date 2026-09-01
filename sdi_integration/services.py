"""
Punto di collegamento tra le fatture emesse e il provider SDI configurato
per la loro azienda. Le funzioni qui sotto sono quello che chiamano le
azioni admin di invoicing/admin.py.
"""
from sdi_integration.models import ConfigurazioneSDI
from sdi_integration.provider import ottieni_provider


def _configurazione_attiva(tenant_id):
    try:
        return ConfigurazioneSDI.objects.get(tenant_id=tenant_id, attivo=True)
    except ConfigurazioneSDI.DoesNotExist:
        raise ValueError("Nessuna configurazione SDI attiva per questa azienda: va configurata dal platform admin prima di poter inviare.")


def invia_fattura_a_sdi(fattura) -> str:
    """Invia una fattura gia' emessa (XML gia' generato) al provider SDI
    configurato per la sua azienda. Aggiorna stato_sdi e
    identificativo_sdi sulla fattura. Ritorna l'identificativo di
    tracking assegnato dal provider."""
    if not fattura.xml_fatturapa:
        raise ValueError("La fattura non ha ancora un XML FatturaPA generato: emettila prima di inviarla.")

    configurazione = _configurazione_attiva(fattura.tenant_id)
    provider = ottieni_provider(configurazione)
    tracking_id = provider.invia_fattura(fattura.xml_fatturapa, configurazione)

    fattura.identificativo_sdi = tracking_id
    fattura.stato_sdi = "INVIATA"
    fattura.save(update_fields=["identificativo_sdi", "stato_sdi"])
    return tracking_id


# I valori esatti di 'marking' restituiti da OpenAPI.it possono variare;
# questa mappa va verificata/ampliata osservando le risposte reali una
# volta iniziato l'uso in produzione.
MAPPA_MARKING_A_STATO = {
    "DONE": "CONSEGNATA",
    "RECEIVED": "INVIATA",
    "ERROR": "SCARTATA",
}


def aggiorna_stato_fattura(fattura) -> dict:
    """Interroga il provider per lo stato aggiornato di una fattura gia'
    inviata, e aggiorna stato_sdi/ricevuta_sdi di conseguenza."""
    if not fattura.identificativo_sdi:
        raise ValueError("La fattura non e' ancora stata inviata a SDI.")

    configurazione = _configurazione_attiva(fattura.tenant_id)
    provider = ottieni_provider(configurazione)
    esito = provider.recupera_stato(configurazione, fattura.identificativo_sdi)

    nuovo_stato = MAPPA_MARKING_A_STATO.get(esito.get("stato"))
    if nuovo_stato:
        fattura.stato_sdi = nuovo_stato
    fattura.ricevuta_sdi = str(esito.get("grezzo", ""))
    fattura.save(update_fields=["stato_sdi", "ricevuta_sdi"])
    return esito
