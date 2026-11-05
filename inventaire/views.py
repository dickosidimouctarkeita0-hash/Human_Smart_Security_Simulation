from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import ObjetForm, CapteurForm, ActionneurForm, MesureForm
from .models import Objet, Capteur, Actionneur, Mesure, Commande, EtatCasque
from .services import commander

CATALOGUE = {
    'objets': (Objet, ObjetForm, 'Objets intelligents'),
    'capteurs': (Capteur, CapteurForm, 'Capteurs'),
    'actionneurs': (Actionneur, ActionneurForm, 'Actionneurs'),
}


def configuration(type_element):
    if type_element not in CATALOGUE:
        raise Http404('Type inconnu')
    return CATALOGUE[type_element]



@login_required
def tableau(request):
    lignes = []

    for capteur in Capteur.objects.select_related('objet'):
        derniere = capteur.mesures.first()

        lignes.append({
            'capteur': capteur,
            'mesure': derniere,
            'alerte': (
                derniere is not None
                and derniere.valeur > capteur.seuil_alerte
            ),
        })

    casques = []

    for objet in Objet.objects.all():
        casques.append({
            'objet': objet,
            'etat': objet.etats_casque.first(),
        })

    
    return render(request, 'inventaire/tableau.html', {
        'nb_objets': Objet.objects.count(),
        'nb_capteurs': Capteur.objects.count(),
        'nb_actionneurs': Actionneur.objects.count(),
        'lignes': lignes,
        'casques': casques,
        'actionneurs': Actionneur.objects.select_related('objet').all(),
    })




@login_required
def liste(request, type_element):
    model, form, titre = configuration(type_element)
    q = request.GET.get('q', '').strip()
    elements = model.objects.filter(nom__icontains=q)
    page = Paginator(elements, 10).get_page(request.GET.get('page'))
    return render(request, 'inventaire/liste.html', {
        'page': page, 'titre': titre, 'type_element': type_element, 'q': q,
    })


@login_required
def fiche(request, type_element, pk):
    model, form, titre = configuration(type_element)
    element = get_object_or_404(model, pk=pk)
    return render(request, 'inventaire/fiche.html', {
        'element': element, 'type_element': type_element,
    })


@login_required
def editer(request, type_element, pk=None):
    model, form_class, titre = configuration(type_element)
    element = get_object_or_404(model, pk=pk) if pk is not None else None
    form = form_class(request.POST if request.method == 'POST' else None, instance=element)
    if request.method == 'POST' and form.is_valid():
        element = form.save()
        messages.success(request, 'Enregistrement réussi.')
        return redirect('fiche', type_element=type_element, pk=element.pk)
    return render(request, 'inventaire/formulaire.html', {
        'form': form, 'titre': ('Modifier : ' if element else 'Ajouter : ') + titre,
        'retour': '/inventaire/' + type_element + '/',
    })


@login_required
def supprimer(request, type_element, pk):
    model, form, titre = configuration(type_element)
    element = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        try:
            element.delete()
        except ProtectedError:
            messages.error(request, 'Suppression refusée : des éléments ou un historique dépendent de cette fiche.')
        else:
            messages.success(request, 'Fiche supprimée.')
            return redirect('liste', type_element=type_element)
    return render(request, 'inventaire/supprimer.html', {
        'element': element, 'type_element': type_element,
    })


@login_required
def mesures(request):
    form = MesureForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mesure ajoutée.')
        return redirect('mesures')
    mesures_qs = Mesure.objects.select_related('capteur', 'capteur__objet')
    capteur_id = request.GET.get('capteur', '')
    if capteur_id:
        capteur = get_object_or_404(Capteur, pk=capteur_id) if capteur_id.isdigit() else None
        if capteur is None:
            raise Http404('Capteur invalide')
        mesures_qs = mesures_qs.filter(capteur=capteur)
    return render(request, 'inventaire/mesures.html', {
        'form': form, 'page': Paginator(mesures_qs, 20).get_page(request.GET.get('page')),
        'capteurs': Capteur.objects.all(), 'filtre': capteur_id,
    })


@login_required
@require_POST
def commande(request, pk):
    get_object_or_404(Actionneur, pk=pk)
    valeur = request.POST.get('etat')
    if valeur not in ('on', 'off'):
        messages.error(request, 'Choisir Marche ou Arrêt.')
    else:
        try:
            commander(pk, request.user, valeur == 'on')
        except ValidationError as erreur:
            messages.error(request, ' '.join(erreur.messages))
        else:
            messages.success(request, 'État simulé enregistré. Aucun matériel réel commandé.')
    if request.POST.get('origine') == 'tableau':
     return redirect('/#commandes-actionneurs')

    return redirect('fiche', type_element='actionneurs', pk=pk)


@login_required
def journal(request):
    commandes = Commande.objects.select_related('actionneur', 'utilisateur')
    return render(request, 'inventaire/journal.html', {
        'page': Paginator(commandes, 20).get_page(request.GET.get('page')),
    })
