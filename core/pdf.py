"""
Rendering PDF condiviso per fatture, DDT e documenti non fiscali. Usa i
template Django (templates/pdf/) per il layout e WeasyPrint per la
conversione HTML+CSS -> PDF: permette di disegnare i documenti con
strumenti normali (HTML/CSS) invece di un linguaggio di layout dedicato.

I template vivono nel codice, quindi sono modificabili SOLO da chi ha
accesso al server (te) — nessun utente cliente puo' toccarli in alcun
modo, coerentemente con il resto del sistema.
"""
import weasyprint
from django.template.loader import render_to_string


def genera_pdf(template_name: str, contesto: dict) -> bytes:
    html = render_to_string(template_name, contesto)
    return weasyprint.HTML(string=html).write_pdf()
