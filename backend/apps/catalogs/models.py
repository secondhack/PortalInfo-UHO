from django.db import models
from django.core.validators import MinValueValidator


class CatalogType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)


class CatalogItem(models.Model):
    catalog = models.ForeignKey(CatalogType, on_delete=models.PROTECT, related_name='items')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['catalog', 'name'], name='unique_catalog_item')]


class Category(models.Model):
    content_type = models.CharField(max_length=12, default='generic', choices=[(x,x) for x in ['generic','news','event','notice','service','survey']])
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    dynamic = models.BooleanField(default=True)
    max_visible = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1)])
    title_limit = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    description_limit = models.PositiveIntegerField(default=300, validators=[MinValueValidator(1)])
    required_fields = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
