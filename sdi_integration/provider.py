"""
Adapter per l'invio delle fatture elettroniche a SDI tramite un
intermediario certificato. Non e' possibile collegarsi direttamente al
Sistema di Interscambio senza accreditamento come intermediario: si passa
sempre da un provider come quello implementato qui sotto.

Riferimento API OpenAPI.it: https://console.openapi.com/it/apis/sdi/documentation
"""
from abc import ABC, abstractmethod

import requests


class SDIProviderAdapter(ABC):
    @abstractmethod
    def invia_fattura(self, xml_fatturapa: str, configurazione) -> str:
        """Invia l'XML al provider. Ritorna un identificativo di tracking."""
        raise NotImplementedError

    @abstractmethod
    def recupera_stato(self, configurazione, identificativo_tracking: str) -> dict:
        """Interroga lo stato di una fattura inviata in precedenza."""
        raise NotImplementedError

    @abstractmethod
    def recupera_fatture_passive(self, configurazione) -> list:
        """Recupera le fatture ricevute (ciclo passivo) per il tenant."""
        raise NotImplementedError


class MockSDIProvider(SDIProviderAdapter):
    """Implementazione finta per sviluppo/test, senza chiamate esterne reali."""

    def invia_fattura(self, xml_fatturapa: str, configurazione) -> str:
        return "MOCK-TRACKING-ID"

    def recupera_stato(self, configurazione, identificativo_tracking: str) -> dict:
        return {"stato": "DONE", "dettaglio": "Esito simulato in ambiente di sviluppo"}

    def recupera_fatture_passive(self, configurazione) -> list:
        return []


class OpenAPIProvider(SDIProviderAdapter):
    """Integrazione con l'API SDI di OpenAPI.it.

    Endpoint usati (produzione: https://sdi.openapi.it, sandbox:
    https://test.sdi.openapi.it — imposta il sandbox in
    ConfigurazioneSDI.api_base_url per fare test senza inviare davvero
    a SDI):
      POST {base}/invoices                — invio fattura XML
      GET  {base}/invoices/{uuid}         — stato di una fattura
      GET  {base}/invoices?type=1         — fatture passive ricevute
      POST {base}/business_registry_configurations — onboarding azienda (una tantum)

    Autenticazione: Bearer token — il campo 'api_key' della
    ConfigurazioneSDI e' il token generato sulla console OpenAPI.it.
    """

    BASE_URL_PRODUZIONE = "https://sdi.openapi.it"

    def _base_url(self, configurazione):
        return (configurazione.api_base_url or self.BASE_URL_PRODUZIONE).rstrip("/")

    def _headers(self, configurazione, content_type="application/json"):
        return {
            "Authorization": f"Bearer {configurazione.api_key}",
            "Content-Type": content_type,
        }

    def invia_fattura(self, xml_fatturapa: str, configurazione) -> str:
        url = f"{self._base_url(configurazione)}/invoices"
        corpo_xml = xml_fatturapa.encode("utf-8") if isinstance(xml_fatturapa, str) else xml_fatturapa
        risposta = requests.post(
            url, data=corpo_xml, headers=self._headers(configurazione, content_type="application/xml"), timeout=30
        )
        risposta.raise_for_status()
        corpo = risposta.json()
        if not corpo.get("success", True):
            raise RuntimeError(f"OpenAPI.it ha rifiutato la fattura: {corpo.get('error') or corpo.get('message')}")
        return corpo["data"]["uuid"]

    def recupera_stato(self, configurazione, identificativo_tracking: str) -> dict:
        url = f"{self._base_url(configurazione)}/invoices/{identificativo_tracking}"
        risposta = requests.get(url, headers=self._headers(configurazione), timeout=30)
        risposta.raise_for_status()
        corpo = risposta.json()
        return {
            "stato": corpo.get("marking") or "SCONOSCIUTO",
            "firmata": corpo.get("signed"),
            "scaricata": corpo.get("downloaded"),
            "avviso": corpo.get("notice"),
            "grezzo": corpo,
        }

    def recupera_fatture_passive(self, configurazione) -> list:
        url = f"{self._base_url(configurazione)}/invoices"
        risposta = requests.get(url, params={"type": 1}, headers=self._headers(configurazione), timeout=30)
        risposta.raise_for_status()
        return risposta.json()

    def crea_configurazione_azienda(self, configurazione, tenant, email_referente: str):
        """Da chiamare UNA SOLA VOLTA per azienda, prima del primo invio:
        registra la partita IVA presso OpenAPI.it (onboarding)."""
        url = f"{self._base_url(configurazione)}/business_registry_configurations"
        payload = {
            "fiscal_id": tenant.partita_iva,
            "name": tenant.ragione_sociale,
            "email": email_referente,
            "apply_signature": False,
            "apply_legal_storage": False,
        }
        risposta = requests.post(url, json=payload, headers=self._headers(configurazione), timeout=30)
        risposta.raise_for_status()
        return risposta.json()


def ottieni_provider(configurazione) -> SDIProviderAdapter:
    """Factory: ritorna l'adapter giusto in base al provider scelto nella
    ConfigurazioneSDI dell'azienda. Punto di estensione per aggiungere
    altri provider (Aruba, Fatture in Cloud...) in futuro."""
    mappa = {
        "OPENAPI": OpenAPIProvider,
    }
    classe = mappa.get(configurazione.provider)
    if classe is None:
        raise NotImplementedError(
            f"Nessun adapter implementato per il provider '{configurazione.get_provider_display()}'. "
            f"Al momento e' disponibile solo OpenAPI.it."
        )
    return classe()
