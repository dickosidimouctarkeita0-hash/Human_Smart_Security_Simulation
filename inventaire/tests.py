from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .forms import MesureForm, CapteurForm
from .models import Objet, Capteur, Actionneur, Mesure, Commande


class ApplicationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('testeur', password='Test-local-827!')
        self.objet = Objet.objects.create(nom='Serre A', emplacement='Laboratoire')
        self.capteur = Capteur.objects.create(
            objet=self.objet, nom='Temperature A', type_mesure='temperature', seuil_alerte=28,
        )
        self.actionneur = Actionneur.objects.create(
            objet=self.objet, nom='Ventilateur A', type_action='ventilateur',
        )

    def connecter_api(self):
        api = APIClient()
        token = Token.objects.create(user=self.user)
        api.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return api

    def test_visiteur_redirige(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.assertEqual(self.client.get('/comptes/login/').status_code, 200)

    def test_connexion_et_pages(self):
        self.assertTrue(self.client.login(username='testeur', password='Test-local-827!'))
        urls = ['/', '/mesures/', '/journal/', '/inventaire/objets/',
                '/inventaire/capteurs/', '/inventaire/actionneurs/',
                '/inventaire/objets/ajouter/',
                f'/inventaire/objets/{self.objet.pk}/',
                f'/inventaire/capteurs/{self.capteur.pk}/',
                f'/inventaire/actionneurs/{self.actionneur.pk}/']
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get('/inventaire/inconnu/').status_code, 404)

    def test_crud_objet_et_protection(self):
        self.client.force_login(self.user)
        r = self.client.post('/inventaire/objets/ajouter/', {
            'nom': 'Bureau', 'emplacement': 'Local B', 'actif': 'on',
        })
        self.assertEqual(r.status_code, 302)
        objet = Objet.objects.get(nom='Bureau')
        self.client.post(f'/inventaire/objets/{objet.pk}/modifier/', {
            'nom': 'Bureau modifie', 'emplacement': 'Local C', 'actif': 'on',
        })
        objet.refresh_from_db()
        self.assertEqual(objet.emplacement, 'Local C')
        self.client.get(f'/inventaire/objets/{objet.pk}/supprimer/')
        self.assertTrue(Objet.objects.filter(pk=objet.pk).exists())
        self.client.post(f'/inventaire/objets/{objet.pk}/supprimer/')
        self.assertFalse(Objet.objects.filter(pk=objet.pk).exists())
        self.client.post(f'/inventaire/objets/{self.objet.pk}/supprimer/')
        self.assertTrue(Objet.objects.filter(pk=self.objet.pk).exists())

    def test_mesure_valide_et_invalide(self):
        self.client.force_login(self.user)
        self.client.post('/mesures/', {'capteur': self.capteur.pk, 'valeur': '30.50'})
        self.assertEqual(Mesure.objects.get().valeur, Decimal('30.50'))
        self.assertContains(self.client.get('/'), 'ALERTE')
        form = MesureForm(data={'capteur': self.capteur.pk, 'valeur': '101'})
        self.assertFalse(form.is_valid())
        self.assertEqual(Mesure.objects.count(), 1)

    def test_historique_protege_type_capteur(self):
        Mesure.objects.create(capteur=self.capteur, valeur=24)
        form = CapteurForm(instance=self.capteur, data={
            'objet': self.objet.pk, 'nom': 'Temperature A',
            'type_mesure': 'humidite', 'seuil_alerte': 60,
        })
        self.assertFalse(form.is_valid())

    def test_commande_post_et_journal(self):
        self.client.force_login(self.user)
        url = f'/commande/{self.actionneur.pk}/'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {'etat': 'on'})
        self.actionneur.refresh_from_db()
        self.assertTrue(self.actionneur.etat)
        self.assertEqual(Commande.objects.get().utilisateur, self.user)
        self.client.post(url, {'etat': 'off'})
        self.actionneur.refresh_from_db()
        self.assertFalse(self.actionneur.etat)
        self.assertEqual(Commande.objects.count(), 2)

    def test_objet_inactif(self):
        self.objet.actif = False
        self.objet.save()
        self.client.force_login(self.user)
        self.client.post(f'/commande/{self.actionneur.pk}/', {'etat': 'on'})
        self.assertEqual(Commande.objects.count(), 0)
        form = MesureForm(data={'capteur': self.capteur.pk, 'valeur': '25'})
        self.assertFalse(form.is_valid())

    def test_csrf_exige(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        r = client.post(f'/commande/{self.actionneur.pk}/', {'etat': 'on'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Commande.objects.count(), 0)

    def test_api_authentification_et_mesure(self):
        self.assertEqual(APIClient().get('/api/objets/').status_code, 401)
        api = self.connecter_api()
        self.assertEqual(api.get('/api/objets/').status_code, 200)
        r = api.post('/api/mesures/', {'capteur': self.capteur.pk, 'valeur': '23.25'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        r = api.post('/api/mesures/', {'capteur': self.capteur.pk, 'valeur': '200'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Mesure.objects.count(), 1)
        self.assertEqual(api.delete(f'/api/mesures/{Mesure.objects.get().pk}/').status_code, 405)

    def test_api_crud_et_commande(self):
        api = self.connecter_api()
        r = api.post('/api/objets/', {'nom': 'B', 'emplacement': 'C', 'actif': True}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        url = f"/api/objets/{r.data['id']}/"
        self.assertEqual(api.patch(url, {'nom': 'C'}, format='json').status_code, 200)
        self.assertEqual(api.delete(url).status_code, 204)
        self.assertEqual(api.delete(f'/api/objets/{self.objet.pk}/').status_code, 400)
        r = api.post(f'/api/actionneurs/{self.actionneur.pk}/commander/', {'etat': 'on'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(r.data['etat'])
        self.assertEqual(Commande.objects.count(), 1)

    def test_api_commande_objet_desactive_refusee(self):
        api = self.connecter_api()
        self.objet.actif = False
        self.objet.save(update_fields=['actif'])
        reponse = api.post(
            f'/api/actionneurs/{self.actionneur.pk}/commander/',
            {'etat': 'on'}, format='json'
        )
        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Commande.objects.count(), 0)
