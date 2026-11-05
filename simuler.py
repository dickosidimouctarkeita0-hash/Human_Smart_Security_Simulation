import argparse
import getpass
import json
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description='Envoyer des mesures simulées à notre API locale.')
parser.add_argument('--capteur', type=int, required=True)
parser.add_argument('--minimum', type=float, default=18)
parser.add_argument('--maximum', type=float, default=35)
parser.add_argument('--nombre', type=int, default=10)
args = parser.parse_args()
if args.minimum > args.maximum or not 1 <= args.nombre <= 100:
    parser.error('Minimum <= maximum; nombre compris entre 1 et 100.')
jeton = getpass.getpass('Collez le jeton API (saisie invisible) : ').strip()
try:
    for numero in range(1, args.nombre + 1):
        valeur = round(random.uniform(args.minimum, args.maximum), 2)
        donnees = json.dumps({'capteur': args.capteur, 'valeur': valeur}).encode('utf-8')
        requete = Request('http://127.0.0.1:8000/api/mesures/', data=donnees, headers={
            'Authorization': 'Token ' + jeton, 'Content-Type': 'application/json',
        }, method='POST')
        with urlopen(requete, timeout=10) as reponse:
            mesure = json.load(reponse)
            print(f"{numero}/{args.nombre} : HTTP {reponse.status}, mesure {mesure['id']}, valeur {mesure['valeur']}")
        if numero < args.nombre:
            time.sleep(2)
except HTTPError as erreur:
    print('API :', erreur.code, erreur.read().decode('utf-8'))
    raise SystemExit(1)
except URLError:
    print('Connexion impossible. Démarrez runserver sur 127.0.0.1:8000.')
    raise SystemExit(1)
except KeyboardInterrupt:
    print('Simulation arrêtée.')
