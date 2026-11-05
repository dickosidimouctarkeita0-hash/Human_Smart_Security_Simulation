from django.core.exceptions import ValidationError as ErreurDjango
from django.db.models.deletion import ProtectedError
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Objet, Capteur, Actionneur, Mesure, Commande
from .serializers import (
    ObjetSerializer, CapteurSerializer, ActionneurSerializer,
    MesureSerializer, CommandeSerializer,
)
from .services import commander


class InventaireViewSet(viewsets.ModelViewSet):
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('Suppression refusée : des éléments ou un historique dépendent de cette fiche.')


class ObjetViewSet(InventaireViewSet):
    queryset = Objet.objects.all()
    serializer_class = ObjetSerializer


class CapteurViewSet(InventaireViewSet):
    queryset = Capteur.objects.select_related('objet').all()
    serializer_class = CapteurSerializer


class ActionneurViewSet(InventaireViewSet):
    queryset = Actionneur.objects.select_related('objet').all()
    serializer_class = ActionneurSerializer

    @action(detail=True, methods=['post'])
    def commander(self, request, pk=None):
        element = self.get_object()
        valeur = request.data.get('etat')
        if valeur not in ('on', 'off'):
            raise ValidationError({'etat': 'Utiliser on ou off.'})
        try:
            element = commander(element.pk, request.user, valeur == 'on')
        except ErreurDjango as erreur:
            raise ValidationError(erreur.messages)
        return Response(self.get_serializer(element).data)


class MesureViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                    mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Mesure.objects.select_related('capteur', 'capteur__objet').all()
    serializer_class = MesureSerializer


class CommandeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Commande.objects.select_related('actionneur', 'utilisateur').all()
    serializer_class = CommandeSerializer
