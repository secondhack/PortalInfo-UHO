from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import User, Role, Grant
from .permissions import role_code


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'code', 'name']
        read_only_fields = ['code']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)

    class Meta:
        model = User
        fields = ['id','email','role','role_name','role_code','is_active','authorized','demo','protected','categories','last_login','password']
        read_only_fields = ['demo','protected','last_login']

    def validate_email(self, value):
        value = value.lower().strip()
        if not value.endswith('@uho.edu.cu') or value.count('@') != 1:
            raise serializers.ValidationError('Utilice un correo institucional @uho.edu.cu.')
        return value

    def validate(self, attrs):
        actor = self.context['request'].user
        target_role = attrs.get('role', self.instance.role if self.instance else None)
        if not target_role:
            raise serializers.ValidationError({'role': 'Seleccione un rol.'})
        if role_code(actor) == 'admin':
            if (self.instance and role_code(self.instance) != 'gestor') or target_role.code != 'gestor':
                raise PermissionDenied('Un Admin solo puede gestionar Gestores.')
        if self.instance and (self.instance.protected or role_code(self.instance) == 'superadmin'):
            if any(k in attrs and attrs[k] != getattr(self.instance,k) for k in ['role','is_active','authorized','email']):
                raise serializers.ValidationError('No puede alterar el acceso del Superadmin protegido.')
        if 'password' in attrs:
            if settings.AUTH_PROVIDER != 'demo' or settings.PRODUCTION or (self.instance and not self.instance.demo):
                raise serializers.ValidationError('Contraseña local solo disponible para identidades demo.')
            try:
                validate_password(attrs['password'])
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': exc.messages})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        categories = validated_data.pop('categories', [])
        user = User(**validated_data, username=validated_data['email'], demo=settings.AUTH_PROVIDER == 'demo')
        user.set_password(password) if password else user.set_unusable_password()
        user.save()
        user.categories.set(categories)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
        user.username = user.email
        user.save()
        return user


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = ['id','user','role','category','operation']

    def validate(self, attrs):
        subject_user = attrs.get('user', getattr(self.instance, 'user', None))
        subject_role = attrs.get('role', getattr(self.instance, 'role', None))
        if bool(subject_user) == bool(subject_role):
            raise serializers.ValidationError('Seleccione exactamente un usuario o un rol.')
        if role_code(self.context['request'].user) == 'admin':
            if not subject_user or role_code(subject_user) != 'gestor':
                raise PermissionDenied('Admin solo asigna permisos a Gestores individuales.')
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=256)
