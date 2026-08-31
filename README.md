# Tasso — gestionale multi-tenant (bozza fase 1)

Tasso: scaffold Django + PostgreSQL per un gestionale multi-azienda con:
clienti/fornitori, catalogo/magazzino, fatturazione (pronta per XML
FatturaPA), DDT, documenti non fiscali.

## Architettura

- **Multi-tenant a schema condiviso**: un solo database, ogni riga di
  business ha un FK `tenant`. Isolamento garantito da
  `core.middleware.TenantMiddleware` + `core.models.TenantManager`
  (filtro automatico sul tenant corrente in ogni queryset).
- **Fatturazione elettronica**: nessun invio diretto a SDI (richiede
  accreditamento come intermediario). Il modulo `sdi_integration`
  espone un adapter (`SDIProviderAdapter`) da implementare per il
  provider scelto (Aruba, OpenAPI.it, Fatture in Cloud...). Per ora è
  presente solo `MockSDIProvider` per sviluppo/test.
- **Magazzino**: le giacenze (`warehouse.Giacenza`) sono denormalizzate
  per letture veloci, ma l'unica scrittura ammessa è
  `warehouse.MovimentoMagazzino` — ogni carico/scarico genera un
  movimento e aggiorna la giacenza in transazione (logica da
  implementare nella fase 2, quando colleghiamo DDT/fatture al
  magazzino).

## Avvio con Docker (consigliato)

Requisiti: solo Docker e Docker Compose installati, nient'altro.

```bash
git clone https://github.com/Hascanio35/tasso.git
cd tasso

docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Nessun file da configurare: le credenziali di comunicazione tra Tasso
(`web`) e il database (`db`) sono già preimpostate di
default in `docker-compose.yml` (utente/password `tasso` su un
database `tasso`, comunicazione interna sulla rete Docker, non
esposta all'esterno). Basta questo per partire in locale/sviluppo.

Se vuoi personalizzare le credenziali (**fortemente consigliato prima
di esporre l'app su internet**, es. su un VPS): copia `.env.example`
in `.env`, cambia almeno `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`, e
`docker compose` lo userà automaticamente al posto dei default
(Compose legge da solo un file `.env` nella cartella del progetto,
senza bisogno di dichiararlo esplicitamente).

```bash
cp .env.example .env   # opzionale, solo per sovrascrivere i default
```

Poi vai su `http://localhost:8000/admin/`. In modalità sviluppo
(default, grazie a `docker-compose.override.yml`) il codice sorgente è
montato come volume: ogni modifica ai file `.py` si riflette subito
senza dover ricostruire l'immagine.

Per un avvio "di produzione" (gunicorn, nessun mount del codice,
nessun reload automatico):

```bash
docker compose -f docker-compose.yml up -d --build
```

**Scaricare l'immagine già pronta invece di ricompilarla**: ogni push
su `main` innesca la GitHub Action in `.github/workflows/docker-publish.yml`,
che pubblica l'immagine su GitHub Container Registry
(`ghcr.io/Hascanio35/tasso`). Chi clona il repo può allora
saltare la build locale e usare direttamente:

```bash
docker compose -f docker-compose.prod.yml up -d
# opzionale: cp .env.example .env per sovrascrivere le credenziali di default
```

(ricorda di rendere il package GHCR pubblico da GitHub → tuo profilo →
Packages, se vuoi che sia scaricabile senza autenticazione).

### Pubblicare il progetto sul tuo GitHub

```bash
cd tasso
git init
git add .
git commit -m "Scaffold iniziale Tasso - gestionale multi-tenant"
git branch -M main
git remote add origin https://github.com/Hascanio35/tasso.git
git push -u origin main
```

Da quel momento la Action builda e pubblica automaticamente l'immagine
ad ogni push su `main` (o quando crei un tag `vX.Y.Z`).

## Setup locale senza Docker (alternativa)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# creare un database postgres "tasso" e un utente "tasso"
# oppure impostare DATABASE_URL in un file .env, es:
# DATABASE_URL=postgres://user:pass@localhost:5432/tasso

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Poi vai su `http://localhost:8000/admin/` — crea prima un `Tenant`,
poi un `User` collegato a quel tenant, per iniziare a inserire
clienti/articoli/fatture.

## Cosa manca (roadmap fase per fase)

1. **Numerazione automatica** — logica di assegnazione `numero`
   progressivo da `SerieNumerazione` (con lock per evitare doppioni in
   concorrenza) per fatture, DDT, documenti non fiscali.
2. **Movimentazione di magazzino automatica** — collegare
   creazione/conferma DDT e fatture immediate allo scarico automatico
   (`MovimentoMagazzino` + aggiornamento `Giacenza`), con controllo
   scorta minima.
3. **Generazione XML FatturaPA** — modulo `fatturapa_builder.py`
   secondo lo schema ufficiale Agenzia Entrate (`lxml`), a partire da
   `Fattura` + `RigaFattura`.
4. **Integrazione provider SDI reale** — implementare
   `SDIProviderAdapter` per il provider scelto (credenziali per
   tenant, cifrate; webhook per ricevere gli esiti di consegna).
5. **API REST** (`clients`, `catalog`, `warehouse`, `invoicing`,
   `ddt`, `documents`) con Django REST Framework, per alimentare un
   frontend dedicato (oggi si lavora solo dal Django admin).
6. **Frontend web** — decidere se Django templates/HTMX (più rapido,
   meno JS) o SPA separata (React) che consuma le API REST.
7. **Generazione PDF** di fatture, DDT e documenti non fiscali.
8. **Permessi granulari** per utente/ruolo all'interno dello stesso
   tenant (oggi solo `is_platform_admin` vs utente normale).
9. **Deploy** — containerizzazione, gestione backup/migrazioni in
   produzione, strategia multi-tenant a livello di dominio (es.
   `cliente1.tuotasso.it`).
