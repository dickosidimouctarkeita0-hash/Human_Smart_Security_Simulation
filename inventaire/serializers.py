from django.core.exceptions import ValidationError as ErreurDjango
from rest_framework import serializers
from .models import Objet, Capteur, Actionneur, Mesure, Commande


class SerializerValide(serializers.ModelSerializer):
    def validate(self, attrs):
        model = self.Meta.model
        instance = self.instance or model()
        for cle, valeur in attrs.items():
            setattr(instance, cle, valeur)
        try:
            instance.full_clean()
        except ErreurDjango as erreur:
            detail = erreur.message_dict if hasattr(erreur, 'message_dict') else erreur.messages
            raise serializers.ValidationError(detail)
        return attrs


class ObjetSerializer(SerializerValide):
    class Meta:
        model = Objet
        fields = ['id', 'nom', 'emplacement', 'description', 'actif']


class CapteurSerializer(SerializerValide):
    unite = serializers.ReadOnlyField()

    class Meta:
        model = Capteur
        fields = ['id', 'objet', 'nom', 'type_mesure', 'seuil_alerte', 'unite']


class ActionneurSerializer(SerializerValide):
    class Meta:
        model = Actionneur
        fields = ['id', 'objet', 'nom', 'type_action', 'etat']
        read_only_fields = ['etat']


class MesureSerializer(SerializerValide):
    class Meta:
        model = Mesure
        fields = ['id', 'capteur', 'valeur', 'date']
        read_only_fields = ['date']


class CommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = ['id', 'actionneur', 'utilisateur', 'etat_demande', 'date']
        read_only_fields = fields
