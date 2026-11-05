
import random
import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from inventaire.models import Objet, Capteur, Mesure, EtatCasque


class Command(BaseCommand):
    help = "Simuler les données des capteurs du casque MineSafe"

    
    def add_arguments(self, parser):
        parser.add_argument(
            "--nombre",
            type=int,
            default=10,
            help="Nombre de cycles de simulation"
        )

        parser.add_argument(
            "--intervalle",
            type=float,
            default=2,
            help="Intervalle entre les cycles en secondes"
        )

    def handle(self, *args, **options):
        nombre = options["nombre"]
        intervalle = options["intervalle"]

        if nombre < 1 or intervalle < 0:
            self.stderr.write(
                "Le nombre doit être positif et l'intervalle non négatif."
            )
            return

        self.stdout.write(
            "=== Démarrage du simulateur MineSafe ==="
        )

        objets = Objet.objects.filter(actif=True)

        if not objets.exists():
            self.stdout.write(
                "Aucun casque actif trouvé."
            )
            return

        for cycle in range(nombre):
            self.stdout.write(
                f"Cycle {cycle + 1}/{nombre}"
            )

            
            for objet in objets:
                self.stdout.write(f"Casque : {objet.nom}")

                # Générer des valeurs simulées
                temperature = round(random.uniform(20, 45), 2)
                humidite = round(random.uniform(30, 85), 2)
                gaz_mq6 = random.randint(350, 900)

                donnees = {
                    "temperature": temperature,
                    "humidite": humidite,
                    "mq6": gaz_mq6,
                }

                # Enregistrer les mesures dans Django
                for type_mesure, valeur in donnees.items():

                    capteur = Capteur.objects.filter(
                        objet=objet,
                        type_mesure=type_mesure
                    ).first()

                    # Créer le capteur MQ-6 s'il n'existe pas
                    if capteur is None and type_mesure == "mq6":
                        capteur = Capteur.objects.create(
                            objet=objet,
                            nom=f"MQ-6 - {objet.nom}",
                            type_mesure="mq6",
                            seuil_alerte=Decimal("700")
                        )

                    if capteur is None:
                        self.stdout.write(
                            f"Capteur {type_mesure} introuvable."
                        )
                        continue

                    Mesure.objects.create(
                        capteur=capteur,
                        valeur=Decimal(str(valeur))
                    )

                    self.stdout.write(
                        f"  {type_mesure} : {valeur} {capteur.unite}"
                    )

                    
                # Simulation de la position GPS
                latitude = round(random.uniform(47.6200, 47.6220), 6)
                longitude = round(random.uniform(-65.6760, -65.6730), 6)

                # Simulation de l'accéléromètre (en g)
                accel_x = round(random.uniform(-0.5, 0.5), 2)
                accel_y = round(random.uniform(-0.5, 0.5), 2)
                accel_z = round(random.uniform(0.8, 1.2), 2)

                # Simulation des événements
                sos = random.random() < 0.05
                choc = random.random() < 0.10

                # Enregistrement de l'état du casque
                EtatCasque.objects.create(
                    objet=objet,
                    latitude=Decimal(str(latitude)),
                    longitude=Decimal(str(longitude)),
                    accel_x=accel_x,
                    accel_y=accel_y,
                    accel_z=accel_z,
                    sos=sos,
                    choc=choc
                )

                # Affichage dans le terminal
                self.stdout.write(
                    f"  GPS : {latitude}, {longitude}"
                )

                self.stdout.write(
                    f"  Accélération : X={accel_x} g, "
                    f"Y={accel_y} g, Z={accel_z} g"
                )

                self.stdout.write(
                    f"  SOS : {'ACTIVÉ' if sos else 'INACTIF'}"
                )

                self.stdout.write(
                    f"  Choc : {'DÉTECTÉ' if choc else 'NON'}"
                )



            if cycle < nombre - 1:
                time.sleep(intervalle)

        self.stdout.write(
            self.style.SUCCESS(
                "Simulation terminée."
            )
        )

