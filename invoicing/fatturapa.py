"""
Generazione dell'XML FatturaPA (schema v1.2, formato FPR12) a partire da
una Fattura gia' emessa (numero assegnato).

Copre il caso comune — fattura B2B/B2C ordinaria a un solo destinatario,
un'unica modalita' di pagamento a saldo, senza bollo virtuale, ritenuta
d'acconto, split payment o riferimenti a fatture PA — che e' la stragrande
maggioranza dei casi per una piccola/media impresa italiana. Se un domani
un cliente ha bisogno di uno di questi casi speciali, si estende questo
file mirati su quel caso, invece di complicare tutto in anticipo per
scenari che potrebbero non presentarsi mai.

Riferimento ufficiale schema: Agenzia delle Entrate, specifiche tecniche
FatturaPA v1.2.x.
"""
from decimal import Decimal

from lxml import etree

NAMESPACE = "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2"


def genera_xml_fatturapa(fattura) -> bytes:
    if not fattura.numero:
        raise ValueError("Impossibile generare l'XML: la fattura non ha ancora un numero assegnato (non emessa)")

    root = etree.Element(f"{{{NAMESPACE}}}FatturaElettronica", nsmap={None: NAMESPACE}, versione="FPR12")

    header = etree.SubElement(root, "FatturaElettronicaHeader")
    _crea_dati_trasmissione(header, fattura)
    _crea_cedente_prestatore(header, fattura.tenant)
    _crea_cessionario_committente(header, fattura.cliente)

    body = etree.SubElement(root, "FatturaElettronicaBody")
    _crea_dati_generali(body, fattura)
    _crea_dati_beni_servizi(body, fattura)
    _crea_dati_pagamento(body, fattura)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _testo(parent, tag, valore):
    el = etree.SubElement(parent, tag)
    el.text = str(valore) if valore not in (None, "") else " "
    return el


def _crea_dati_trasmissione(header, fattura):
    dt = etree.SubElement(header, "DatiTrasmissione")
    id_trasmittente = etree.SubElement(dt, "IdTrasmittente")
    _testo(id_trasmittente, "IdPaese", "IT")
    _testo(id_trasmittente, "IdCodice", fattura.tenant.partita_iva)
    # progressivo univoco: usiamo la chiave primaria della fattura,
    # sempre unica nel sistema — evita di dover mantenere un contatore
    # di invio separato solo per questo campo
    _testo(dt, "ProgressivoInvio", str(fattura.pk).zfill(5))
    _testo(dt, "FormatoTrasmissione", "FPR12")
    codice_dest = fattura.cliente.codice_destinatario_sdi or "0000000"
    _testo(dt, "CodiceDestinatario", codice_dest)
    if codice_dest == "0000000" and fattura.cliente.pec_fatturazione:
        _testo(dt, "PECDestinatario", fattura.cliente.pec_fatturazione)


def _crea_cedente_prestatore(header, tenant):
    cp = etree.SubElement(header, "CedentePrestatore")
    da = etree.SubElement(cp, "DatiAnagrafici")
    iva = etree.SubElement(da, "IdFiscaleIVA")
    _testo(iva, "IdPaese", "IT")
    _testo(iva, "IdCodice", tenant.partita_iva)
    if tenant.codice_fiscale:
        _testo(da, "CodiceFiscale", tenant.codice_fiscale)
    anagrafica = etree.SubElement(da, "Anagrafica")
    _testo(anagrafica, "Denominazione", tenant.ragione_sociale)
    _testo(da, "RegimeFiscale", tenant.regime_fiscale or "RF01")
    sede = etree.SubElement(cp, "Sede")
    _testo(sede, "Indirizzo", tenant.indirizzo or "n.d.")
    _testo(sede, "CAP", tenant.cap or "00000")
    _testo(sede, "Comune", tenant.citta or "n.d.")
    if tenant.provincia:
        _testo(sede, "Provincia", tenant.provincia)
    _testo(sede, "Nazione", "IT")


def _crea_cessionario_committente(header, cliente):
    cc = etree.SubElement(header, "CessionarioCommittente")
    da = etree.SubElement(cc, "DatiAnagrafici")
    if cliente.partita_iva:
        iva = etree.SubElement(da, "IdFiscaleIVA")
        _testo(iva, "IdPaese", "IT")
        _testo(iva, "IdCodice", cliente.partita_iva)
    if cliente.codice_fiscale:
        _testo(da, "CodiceFiscale", cliente.codice_fiscale)
    anagrafica = etree.SubElement(da, "Anagrafica")
    if cliente.tipo_soggetto == "PF" and " " in cliente.ragione_sociale.strip():
        # persona fisica: lo schema vuole Nome+Cognome separati.
        # Approssimazione: split sull'ultimo spazio del nome inserito.
        # Per i clienti aziendali (PG, il caso tipico B2B) non si applica.
        parti = cliente.ragione_sociale.rsplit(" ", 1)
        _testo(anagrafica, "Nome", parti[0])
        _testo(anagrafica, "Cognome", parti[1])
    else:
        _testo(anagrafica, "Denominazione", cliente.ragione_sociale)
    sede = etree.SubElement(cc, "Sede")
    _testo(sede, "Indirizzo", cliente.indirizzo or "n.d.")
    _testo(sede, "CAP", cliente.cap or "00000")
    _testo(sede, "Comune", cliente.citta or "n.d.")
    if cliente.provincia:
        _testo(sede, "Provincia", cliente.provincia)
    _testo(sede, "Nazione", cliente.nazione or "IT")


def _crea_dati_generali(body, fattura):
    dg = etree.SubElement(body, "DatiGenerali")
    dgd = etree.SubElement(dg, "DatiGeneraliDocumento")
    _testo(dgd, "TipoDocumento", fattura.tipo_documento_sdi)
    _testo(dgd, "Divisa", "EUR")
    _testo(dgd, "Data", fattura.data_documento.isoformat())
    _testo(dgd, "Numero", f"{fattura.serie.codice}-{fattura.numero}")
    _testo(dgd, "ImportoTotaleDocumento", f"{fattura.totale:.2f}")
    if fattura.note:
        _testo(dgd, "Causale", fattura.note[:200])


def _crea_dati_beni_servizi(body, fattura):
    dbs = etree.SubElement(body, "DatiBeniServizi")
    riepiloghi = {}  # (aliquota, natura) -> [imponibile, imposta]

    for riga in fattura.righe.all().order_by("numero_riga"):
        dl = etree.SubElement(dbs, "DettaglioLinee")
        _testo(dl, "NumeroLinea", riga.numero_riga)
        _testo(dl, "Descrizione", riga.descrizione)
        _testo(dl, "Quantita", f"{riga.quantita:.2f}")
        _testo(dl, "PrezzoUnitario", f"{riga.prezzo_unitario:.4f}")
        if riga.sconto_percentuale:
            sconto_wrap = etree.SubElement(dl, "ScontoMaggiorazione")
            _testo(sconto_wrap, "Tipo", "SC")
            _testo(sconto_wrap, "Percentuale", f"{riga.sconto_percentuale:.2f}")
        imponibile_riga = riga.imponibile_riga
        _testo(dl, "PrezzoTotale", f"{imponibile_riga:.2f}")
        _testo(dl, "AliquotaIVA", f"{riga.aliquota_iva:.2f}")
        if riga.aliquota_iva == 0 and riga.natura_iva:
            _testo(dl, "Natura", riga.natura_iva)

        chiave = (riga.aliquota_iva, riga.natura_iva)
        acc = riepiloghi.setdefault(chiave, [Decimal("0"), Decimal("0")])
        acc[0] += imponibile_riga
        acc[1] += imponibile_riga * riga.aliquota_iva / 100

    for (aliquota, natura), (imponibile, imposta) in riepiloghi.items():
        dr = etree.SubElement(dbs, "DatiRiepilogo")
        _testo(dr, "AliquotaIVA", f"{aliquota:.2f}")
        if aliquota == 0 and natura:
            _testo(dr, "Natura", natura)
        _testo(dr, "ImponibileImporto", f"{imponibile:.2f}")
        _testo(dr, "Imposta", f"{imposta:.2f}")
        _testo(dr, "EsigibilitaIVA", "I")


def _crea_dati_pagamento(body, fattura):
    dp = etree.SubElement(body, "DatiPagamento")
    _testo(dp, "CondizioniPagamento", "TP02")  # pagamento completo a saldo
    dett = etree.SubElement(dp, "DettaglioPagamento")
    _testo(dett, "ModalitaPagamento", "MP05")  # bonifico bancario
    _testo(dett, "ImportoPagamento", f"{fattura.totale:.2f}")
    if fattura.tenant.iban:
        _testo(dett, "IBAN", fattura.tenant.iban)
