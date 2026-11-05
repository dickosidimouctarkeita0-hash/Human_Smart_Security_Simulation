from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Objet(models.Model):
    nom = models.CharField(max_length=80, unique=True)
    emplacement = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Capteur(models.Model):
    TYPES = [('temperature', 'Température'),('humidite', 'Humidité'),('mq6', 'Gaz MQ-6 (brut)'),]
    objet = models.ForeignKey(Objet, on_delete=models.PROTECT, related_name='capteurs')
    nom = models.CharField(max_length=80, unique=True)
    type_mesure = models.CharField(max_length=20, choices=TYPES)
    seuil_alerte = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        ordering = ['nom']

   
    @property
    def unite(self):
        return {
        'temperature': '°C',
        'humidite': '%',
        'mq6': 'brut',
    }.get(self.type_mesure, '')


    
    @property
    def bornes(self):
        return {
        'temperature': (-50, 100),
        'humidite': (0, 100),
        'mq6': (0, 4095),
    }.get(self.type_mesure, (0, 100))


    def clean(self):
        if self.seuil_alerte is not None:
            bas, haut = self.bornes
            if not bas <= self.seuil_alerte <= haut:
                raise ValidationError({'seuil_alerte': f'Choisir une valeur entre {bas} et {haut}.'})
        if self.pk and self.mesures.exists():
            ancien = Capteur.objects.get(pk=self.pk)
            if ancien.type_mesure != self.type_mesure or ancien.objet_id != self.objet_id:
                raise ValidationError('Avec un historique, le type et l’objet du capteur sont fixes.')

    def __str__(self):
        return f'{self.nom} ({self.unite})'


class Actionneur(models.Model):
    objet = models.ForeignKey(Objet, on_delete=models.PROTECT, related_name='actionneurs')
    nom = models.CharField(max_length=80, unique=True)
    type_action = models.CharField(max_length=20, choices=[
        ('lampe', 'Lampe'),
    ])
    etat = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ['nom']

    def clean(self):
        if self.pk and self.commandes.exists():
            ancien = Actionneur.objects.get(pk=self.pk)
            if ancien.objet_id != self.objet_id or ancien.type_action != self.type_action:
                raise ValidationError('Avec un historique, le type et l’objet de l’actionneur sont fixes.')

    def __str__(self):
        return self.nom


class Mesure(models.Model):
    capteur = models.ForeignKey(Capteur, on_delete=models.PROTECT, related_name='mesures')
    valeur = models.DecimalField(max_digits=7, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def clean(self):
        if self.capteur_id:
            if not self.capteur.objet.actif:
                raise ValidationError({'capteur': 'Cet objet est désactivé.'})
            bas, haut = self.capteur.bornes
            if self.valeur is not None and not bas <= self.valeur <= haut:
                raise ValidationError({'valeur': f'Valeur attendue entre {bas} et {haut}.'})


class Commande(models.Model):
    actionneur = models.ForeignKey(Actionneur, on_delete=models.PROTECT, related_name='commandes')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    etat_demande = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']


class EtatCasque(models.Model):
    """Données simulées du GPS, accéléromètre et SOS."""

    objet = models.ForeignKey(
        Objet,
        on_delete=models.PROTECT,
        related_name='etats_casque'
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6
    )

    accel_x = models.FloatField()
    accel_y = models.FloatField()
    accel_z = models.FloatField()

    sos = models.BooleanField(default=False)
    choc = models.BooleanField(default=False)

    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def clean(self):
        if (
            not -90 <= self.latitude <= 90
            or not -180 <= self.longitude <= 180
        ):
            raise ValidationError(
                'Coordonnées GPS invalides.'
            )

        if not self.objet.actif:
            raise ValidationError('Casque désactivé.')

    def __str__(self):
        return f'{self.objet.nom} - {self.date}'
