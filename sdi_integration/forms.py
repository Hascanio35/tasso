from django import forms

from sdi_integration.models import ConfigurazioneSDI


class ConfigurazioneSDIForm(forms.ModelForm):
    """I campi credenziale qui sotto sono 'virtuali' (non esistono sul
    modello): servono solo per l'inserimento in chiaro nel form. Non
    vengono mai precompilati con il valore esistente (write-only, come
    un campo password) e, se lasciati vuoti, il valore gia' salvato non
    viene toccato — cosi' si puo' modificare il provider o le note
    senza dover reinserire tutte le credenziali ogni volta."""

    api_key = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Lascia vuoto per non modificare il valore gia' salvato",
    )
    client_id = forms.CharField(required=False, help_text="Lascia vuoto per non modificare il valore gia' salvato")
    client_secret = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Lascia vuoto per non modificare il valore gia' salvato",
    )
    username_provider = forms.CharField(
        required=False, label="Username", help_text="Lascia vuoto per non modificare il valore gia' salvato"
    )
    password_provider = forms.CharField(
        required=False, label="Password", widget=forms.PasswordInput(render_value=False),
        help_text="Lascia vuoto per non modificare il valore gia' salvato",
    )

    class Meta:
        model = ConfigurazioneSDI
        # 'tenant' NON e' escluso qui: e' il platform admin a scegliere
        # esplicitamente per quale azienda sta configurando il provider.
        exclude = [
            "api_key_cifrata", "client_id_cifrato", "client_secret_cifrato",
            "username_cifrato", "password_cifrata",
        ]

    def save(self, commit=True):
        istanza = super().save(commit=False)
        for campo in ["api_key", "client_id", "client_secret", "username_provider", "password_provider"]:
            valore = self.cleaned_data.get(campo)
            if valore:
                setattr(istanza, campo, valore)
        if commit:
            istanza.save()
        return istanza
