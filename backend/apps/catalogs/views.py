from rest_framework.exceptions import PermissionDenied
from apps.accounts.views import AuditedViewSet
from apps.accounts.permissions import role_code
from .models import Category, CatalogItem, CatalogType
from .serializers import CategorySerializer, CatalogItemSerializer, CatalogTypeSerializer


class CategoryViewSet(AuditedViewSet):
    queryset = Category.objects.order_by('id')
    serializer_class = CategorySerializer
    search_fields = ['name','slug']
    filterset_fields = ['active','visible','dynamic']

    def perform_create(self, serializer):
        if role_code(self.request.user) != 'superadmin':
            raise PermissionDenied('Solo el Superadmin crea categorías.')
        super().perform_create(serializer)

    def perform_update(self, serializer):
        if role_code(self.request.user) != 'superadmin' and set(serializer.validated_data) - {'visible','max_visible','title_limit','description_limit'}:
            raise PermissionDenied('Admin solo configura visibilidad y límites.')
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if role_code(self.request.user) != 'superadmin':
            raise PermissionDenied('Solo el Superadmin elimina categorías.')
        super().perform_destroy(instance)


class CatalogTypeViewSet(AuditedViewSet):
    queryset = CatalogType.objects.order_by('id')
    serializer_class = CatalogTypeSerializer
    search_fields = ['name']


class CatalogItemViewSet(AuditedViewSet):
    queryset = CatalogItem.objects.order_by('id')
    serializer_class = CatalogItemSerializer
    filterset_fields = ['catalog','active','parent']
    search_fields = ['name']
