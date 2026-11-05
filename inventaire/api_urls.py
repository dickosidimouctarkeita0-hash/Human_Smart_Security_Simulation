from rest_framework.routers import DefaultRouter
from .api import ObjetViewSet, CapteurViewSet, ActionneurViewSet, MesureViewSet, CommandeViewSet

router = DefaultRouter()
router.register('objets', ObjetViewSet)
router.register('capteurs', CapteurViewSet)
router.register('actionneurs', ActionneurViewSet)
router.register('mesures', MesureViewSet)
router.register('commandes', CommandeViewSet)
urlpatterns = router.urls
