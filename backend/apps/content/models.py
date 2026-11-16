from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Content(models.Model):
    revision = models.PositiveIntegerField(default=1)
    deleted_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    seed_key = models.CharField(max_length=100, null=True, blank=True, unique=True, editable=False)
    live_publication = models.ForeignKey('Publication', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    class State(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'
        HIDDEN = 'hidden', 'Oculto'
    category = models.ForeignKey('catalogs.Category', on_delete=models.PROTECT, related_name='contents')
    title = models.TextField()
    description = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    state = models.CharField(max_length=12, choices=State.choices, default=State.DRAFT)
    validity = models.CharField(max_length=15, choices=[(x, x) for x in ['today','three_days','week','month','always','custom']], default='three_days')
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    manual_active = models.BooleanField(default=True)
    extra_fields = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['category','state','starts_at','ends_at'])]
        constraints = [models.CheckConstraint(condition=models.Q(ends_at__isnull=True) | models.Q(ends_at__gt=models.F('starts_at')), name='content_valid_dates')]

    def clean(self):
        errors = {}
        if len(self.title) > self.category.title_limit:
            errors['title'] = 'Supera el límite de la categoría.'
        if len(self.description) > self.category.description_limit:
            errors['description'] = 'Supera el límite de la categoría.'
        if self.ends_at and self.ends_at <= self.starts_at:
            errors['ends_at'] = 'La fecha final debe ser posterior a la inicial.'
        if errors:
            raise ValidationError(errors)

    @property
    def effectively_visible(self):
        from .queries import is_public
        return is_public(self)


class News(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True)
    area = models.ForeignKey('catalogs.CatalogItem', on_delete=models.PROTECT)
    external_url = models.URLField(blank=True)


class Event(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True)
    area = models.ForeignKey('catalogs.CatalogItem', on_delete=models.PROTECT)
    event_at = models.DateTimeField()
    contact = models.CharField(max_length=250)
    invitation_url = models.URLField(blank=True)


class Service(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True)
    access_url = models.URLField()
    area = models.ForeignKey('catalogs.CatalogItem', on_delete=models.PROTECT, null=True, blank=True)
    service_type = models.ForeignKey('catalogs.CatalogItem', on_delete=models.PROTECT, null=True, blank=True, related_name='services')


class Survey(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE, primary_key=True)
    external_url = models.URLField(blank=True)


class Question(models.Model):
    required = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    kind = models.CharField(max_length=10, choices=[('single','Simple'),('multiple','Múltiple'),('open','Abierta')])
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'pk']
        constraints = [models.UniqueConstraint(fields=['survey','position'], condition=models.Q(archived=False), name='active_question_position')]


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300)


class Response(models.Model):
    submission = models.ForeignKey('Submission', null=True, blank=True, on_delete=models.PROTECT, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    respondent_key = models.CharField(max_length=128)
    value = models.TextField(blank=True)
    options = models.ManyToManyField(Option, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['submission','question'], name='one_answer_per_question')]


class Publication(models.Model):
    content = models.ForeignKey(Content, on_delete=models.PROTECT, related_name='publications')
    category = models.ForeignKey('catalogs.Category', on_delete=models.PROTECT, related_name='publications')
    version = models.PositiveIntegerField()
    data = models.JSONField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_recorded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['content','version'],name='unique_publication_version')]
        indexes = [models.Index(fields=['category','starts_at','ends_at'])]


class Submission(models.Model):
    demo=models.BooleanField(default=False)
    seed_key=models.CharField(max_length=120,null=True,blank=True,unique=True)
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='submissions')
    respondent_key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['publication','respondent_key'],name='unique_survey_submission')]
