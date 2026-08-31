"""
Adapter per l'invio delle fatture elettroniche a SDI tramite un
intermediario certificato (Aruba, OpenAPI.it, Fatture in Cloud, ecc).

Non e' possibile collegarsi direttamente al Sistema di Interscambio senza
accreditamento come intermediario: qualunque provider si scelga, il flusso
e' sempre:
  1. generiamo l'XML FatturaPA (vedi sdi_integration/fatturapa_builder.py,
     da implementare secondo lo schema ufficiale dell'Agenzia delle Entrate)
  2. lo passiamo al provider via la sua API REST
  3. il provider inoltra a SDI e ci restituisce (via webhook o polling)
     gli esiti: consegnata, scartata, mancata consegna, decorrenza termini

Questa interfaccia astratta permette di cambiare provider (o di testare
con un mock) senza toccare invoicing/*.
"""
from abc import ABC, abstractmethod


class SDIProviderAdapter(ABC):
    @abstractmethod
    def invia_fattura(self, xml_fatturapa: str, tenant_config: dict) -> str:
        """Invia l'XML al provider. Ritorna un identificativo di tracking."""
        raise NotImplementedError

    @abstractmethod
    def recupera_stato(self, identificativo_tracking: str) -> dict:
        """Interroga lo stato di una fattura inviata in precedenza."""
        raise NotImplementedError

    @abstractmethod
    def recupera_fatture_passive(self, tenant_config: dict) -> list[dict]:
        """Recupera le fatture ricevute (ciclo passivo) per il tenant."""
        raise NotImplementedError


class MockSDIProvider(SDIProviderAdapter):
    """Implementazione finta per sviluppo/test, senza chiamate esterne reali."""

    def invia_fattura(self, xml_fatturapa: str, tenant_config: dict) -> str:
        return "MOCK-TRACKING-ID"

    def recupera_stato(self, identificativo_tracking: str) -> dict:
        return {"stato": "CONSEGNATA", "dettaglio": "Esito simulato in ambiente di sviluppo"}

    def recupera_fatture_passive(self, tenant_config: dict) -> list[dict]:
        return []


# Punto di estensione: implementare qui es. ArubaSDIProvider(SDIProviderAdapter)
# o OpenAPISDIProvider(SDIProviderAdapter) con le rispettive chiamate REST,
# credenziali per tenant (salvate cifrate, non nel modello Tenant in chiaro),
# e selezionarlo in base a settings/tenant.
