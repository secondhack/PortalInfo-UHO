from rest_framework import serializers
from .models import Category, CatalogType, CatalogItem


class CategorySerializer(serializers.ModelSerializer):
    def validate_slug(self,value):
        if self.instance and not self.instance.dynamic and value!=self.instance.slug:
            raise serializers.ValidationError('La ruta de una categoría base debe mantenerse estable.')
        if value in {'config','categorias','admin','csrf','me','health','schema','docs','vistas','demo'}:
            raise serializers.ValidationError('Este slug está reservado para rutas del sistema.')
        return value

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'dynamic', 'content_type']

    def validate_required_fields(self, value):
        if not isinstance(value, list) or any(not isinstance(x, str) or len(x) > 80 for x in value):
            raise serializers.ValidationError('Debe ser una lista de nombres de campos.')
        return value


class CatalogTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogType
        fields = '__all__'


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate(self, attrs):
        parent = attrs.get('parent')
        visited = {self.instance.pk} if self.instance else set()
        while parent:
            if parent.pk in visited:
                raise serializers.ValidationError('La jerarquía no puede contener ciclos.')
            visited.add(parent.pk)
            parent = parent.parent
        return attrs
