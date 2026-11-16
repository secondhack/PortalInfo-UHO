from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Role(models.Model):
    class Code(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Superadmin'
        ADMIN = 'admin', 'Admin'
        MANAGER = 'gestor', 'Gestor de Contenidos'
    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100)


class User(AbstractUser):
    username = models.CharField(max_length=254, unique=True)
    email = models.EmailField(unique=True, validators=[RegexValidator(r'^[^@\s]+@uho\.edu\.cu$', 'Utilice un correo @uho.edu.cu.')])
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True)
    demo = models.BooleanField(default=False)
    protected = models.BooleanField(default=False, editable=False)
    authorized = models.BooleanField(default=True)
    aga_uid = models.CharField(max_length=150, blank=True, unique=True, null=True)
    categories = models.ManyToManyField('catalogs.Category', blank=True)

    def delete(self, *args, **kwargs):
        if self.protected or (self.role and self.role.code == Role.Code.SUPERADMIN):
            raise ValidationError('El Superadmin no puede eliminarse.')
        return super().delete(*args, **kwargs)


class Grant(models.Model):
    class Operation(models.TextChoices):
        VIEW = 'view', 'Consultar'
        CREATE = 'create', 'Crear'
        EDIT = 'edit', 'Editar'
        DELETE = 'delete', 'Eliminar'
        SUBMIT = 'submit', 'Enviar a aprobación'
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='category_grants')
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.CASCADE, related_name='category_grants')
    category = models.ForeignKey('catalogs.Category', on_delete=models.CASCADE)
    operation = models.CharField(max_length=12, choices=Operation.choices)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(models.Q(user__isnull=False, role__isnull=True) | models.Q(user__isnull=True, role__isnull=False)), name='grant_one_subject'),
            models.UniqueConstraint(fields=['user', 'category', 'operation'], name='unique_user_grant'),
            models.UniqueConstraint(fields=['role', 'category', 'operation'], name='unique_role_grant')]
