"""
Crea (o aggiorna) i ruoli standard da assegnare agli utenti delle aziende
clienti. Idempotente: si puo' rilanciare in qualsiasi momento (es. dopo
aver aggiunto un nuovo modulo) per sincronizzare i permessi dei gruppi
alla definizione qui sotto, senza duplicare nulla.

Uso:
    python manage.py crea_ruoli_base
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q

# App di business "normali": tutto cio' che un'azienda cliente puo' usare.
# 'core' e' volutamente escluso: Aziende/Utenti/Contatori restano
# accessibili solo ai platform admin (vedi core/admin.py), qualunque
# permesso venga assegnato qui.
APP_DI_BUSINESS = ["clients", "catalog", "warehouse", "invoicing", "ddt", "documents"]

RUOLI = {
    "Amministrazione": {
        "apps": APP_DI_BUSINESS,
        "azioni": ["add", "change", "delete", "view"],
    },
    "Magazziniere": {
        "modelli": [
            ("ddt", "documentotrasporto", ["add", "change", "view"]),
            ("ddt", "rigaddt", ["add", "change", "view"]),
            ("warehouse", "magazzino", ["view"]),
            ("warehouse", "giacenza", ["view"]),
            ("warehouse", "movimentomagazzino", ["view"]),
            ("catalog", "articolo", ["view"]),
            ("catalog", "categoriaarticolo", ["view"]),
            ("clients", "anagrafica", ["view"]),
            ("clients", "indirizzospedizione", ["view"]),
        ],
    },
    "Sola lettura": {
        "apps": APP_DI_BUSINESS,
        "azioni": ["view"],
    },
}


class Command(BaseCommand):
    help = "Crea o aggiorna i gruppi/ruoli standard (Amministrazione, Magazziniere, Sola lettura)."

    def handle(self, *args, **options):
        for nome, config in RUOLI.items():
            gruppo, creato = Group.objects.get_or_create(name=nome)

            if "apps" in config:
                content_types = ContentType.objects.filter(app_label__in=config["apps"])
                azioni_q = Q()
                for azione in config["azioni"]:
                    azioni_q |= Q(codename__startswith=f"{azione}_")
                permessi = list(Permission.objects.filter(content_type__in=content_types).filter(azioni_q))
            else:
                permessi = []
                for app_label, model_name, azioni in config["modelli"]:
                    try:
                        ct = ContentType.objects.get(app_label=app_label, model=model_name)
                    except ContentType.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Modello {app_label}.{model_name} non trovato (migrazioni non applicate?), salto."
                        ))
                        continue
                    azioni_q = Q()
                    for azione in azioni:
                        azioni_q |= Q(codename__startswith=f"{azione}_")
                    permessi += list(Permission.objects.filter(content_type=ct).filter(azioni_q))

            gruppo.permissions.set(permessi)
            stato = "creato" if creato else "aggiornato"
            self.stdout.write(self.style.SUCCESS(f"Gruppo '{nome}' {stato} con {len(permessi)} permessi."))
