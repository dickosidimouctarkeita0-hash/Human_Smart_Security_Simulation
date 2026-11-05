
from django.contrib import admin

from .models import (
    Objet,
    Capteur,
    Actionneur,
    Mesure,
    Commande,
    EtatCasque,
)


admin.site.register([Objet, Capteur, Actionneur])


@admin.register(Mesure, Commande)
class HistoriqueAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EtatCasque)
class EtatCasqueAdmin(admin.ModelAdmin):

    list_display = (
        'objet',
        'latitude',
        'longitude',
        'sos',
        'choc',
        'date',
    )

    list_filter = (
        'objet',
        'sos',
        'choc',
    )

    readonly_fields = (
        'objet',
        'latitude',
        'longitude',
        'accel_x',
        'accel_y',
        'accel_z',
        'sos',
        'choc',
        'date',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
