from core.pdf import genera_pdf


def genera_pdf_documento(documento) -> bytes:
    contesto = {
        "documento": documento,
        "tenant": documento.tenant,
        "righe": documento.righe.select_related("articolo").order_by("numero_riga"),
    }
    return genera_pdf("pdf/documento_non_fiscale.html", contesto)
