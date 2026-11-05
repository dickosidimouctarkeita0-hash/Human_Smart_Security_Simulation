from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Actionneur, Commande


@transaction.atomic
def commander(actionneur_id, utilisateur, etat):
    actionneur = Actionneur.objects.select_for_update().get(pk=actionneur_id)
    if not actionneur.objet.actif:
        raise ValidationError('Objet désactivé : commande refusée.')
    actionneur.etat = etat
    actionneur.save(update_fields=['etat'])
    Commande.objects.create(
        actionneur=actionneur, utilisateur=utilisateur, etat_demande=etat,
    )
    return actionneur
