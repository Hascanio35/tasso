from core.pdf import genera_pdf


def genera_pdf_fattura(fattura) -> bytes:
    contesto = {
        "fattura": fattura,
        "tenant": fattura.tenant,
        "righe": fattura.righe.select_related("articolo").order_by("numero_riga"),
    }
    return genera_pdf("pdf/fattura.html", contesto)
