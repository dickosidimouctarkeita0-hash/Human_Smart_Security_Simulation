from django import forms
from .models import Objet, Capteur, Actionneur, Mesure


class ObjetForm(forms.ModelForm):
    class Meta:
        model = Objet
        fields = ['nom', 'emplacement', 'description', 'actif']


class CapteurForm(forms.ModelForm):
    class Meta:
        model = Capteur
        fields = ['objet', 'nom', 'type_mesure', 'seuil_alerte']


class ActionneurForm(forms.ModelForm):
    class Meta:
        model = Actionneur
        fields = ['objet', 'nom', 'type_action']


class MesureForm(forms.ModelForm):
    class Meta:
        model = Mesure
        fields = ['capteur', 'valeur']
