"""
Cifratura simmetrica (Fernet, AES-128 sotto il cofano) delle credenziali
dei provider SDI. Le credenziali di un cliente terzo (Aruba, OpenAPI.it,
ecc.) non vanno mai salvate in chiaro nel database, a differenza dei
normali dati di business.

La chiave vive in settings.SDI_ENCRYPTION_KEY (variabile d'ambiente
SDI_ENCRYPTION_KEY), separata da DJANGO_SECRET_KEY: ruotare l'una non
deve invalidare l'altra. Va generata una volta con:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
e va tenuta al sicuro quanto una password — se si perde, le
credenziali gia' salvate non sono piu' decifrabili (andranno reinserite).
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet():
    return Fernet(settings.SDI_ENCRYPTION_KEY.encode())


def cifra(testo: str) -> str:
    if not testo:
        return ""
    return _fernet().encrypt(testo.encode()).decode()


def decifra(testo_cifrato: str) -> str:
    if not testo_cifrato:
        return ""
    try:
        return _fernet().decrypt(testo_cifrato.encode()).decode()
    except InvalidToken:
        # chiave cambiata o dato corrotto: meglio segnalarlo chiaramente
        # che restituire un valore silenziosamente sbagliato
        return "‹non decifrabile: SDI_ENCRYPTION_KEY diversa da quella usata al salvataggio›"
