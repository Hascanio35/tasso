"""
Invia a SDI le fatture emesse da almeno N giorni, dove N e' il ritardo
configurato per ciascuna azienda in Tenant.giorni_attesa_invio_sdi (sezione
Aziende, modificabile solo dal platform admin).

Pensato per essere lanciato periodicamente da un processo in background
(vedi il servizio 'scheduler' in docker-compose.yml), non manualmente —
anche se puoi comunque lanciarlo a mano per testare:
    python manage.py invia_fatture_scadute

L'invio manuale immediato (azione 'Invia a SDI' nell'admin) resta sempre
disponibile e indipendente da questo: chi vuole spedire subito una
fattura non deve aspettare il giro schedulato.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from invoicing.models import Fattura
from sdi_integration.models import ConfigurazioneSDI
from sdi_integration.services import invia_fattura_a_sdi


class Command(BaseCommand):
    help = "Invia a SDI le fatture emesse da abbastanza tempo, secondo il ritardo configurato per azienda."

    def handle(self, *args, **options):
        adesso = timezone.now()
        totale_inviate = 0
        totale_errori = 0

        for configurazione in ConfigurazioneSDI.objects.filter(attivo=True).select_related("tenant"):
            soglia = adesso - timedelta(days=configurazione.tenant.giorni_attesa_invio_sdi)
            fatture_da_inviare = Fattura.objects.filter(
                tenant_id=configurazione.tenant_id,
                confermata=True,
                stato_sdi="DA_INVIARE",
                emesso_il__lte=soglia,
            )
            for fattura in fatture_da_inviare:
                try:
                    invia_fattura_a_sdi(fattura)
                    totale_inviate += 1
                    self.stdout.write(self.style.SUCCESS(f"Inviata: {fattura}"))
                except Exception as errore:
                    totale_errori += 1
                    self.stdout.write(self.style.ERROR(f"Errore inviando {fattura}: {errore}"))

        if totale_inviate == 0 and totale_errori == 0:
            self.stdout.write("Nessuna fattura da inviare in questo giro.")
        else:
            self.stdout.write(f"Giro completato: {totale_inviate} inviate, {totale_errori} errori.")
