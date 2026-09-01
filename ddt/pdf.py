from core.pdf import genera_pdf


def genera_pdf_ddt(ddt) -> bytes:
    contesto = {
        "ddt": ddt,
        "tenant": ddt.tenant,
        "righe": ddt.righe.select_related("articolo").order_by("numero_riga"),
    }
    return genera_pdf("pdf/ddt.html", contesto)
