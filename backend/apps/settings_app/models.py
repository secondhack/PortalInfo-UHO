from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class GlobalSettings(models.Model):
    security_window_minutes=models.PositiveIntegerField(default=30,validators=[MinValueValidator(5),MaxValueValidator(1440)])
    security_ip_threshold=models.PositiveIntegerField(default=3,validators=[MinValueValidator(2),MaxValueValidator(100)])
    security_device_threshold=models.PositiveIntegerField(default=3,validators=[MinValueValidator(2),MaxValueValidator(100)])
    security_activity_threshold=models.PositiveIntegerField(default=20,validators=[MinValueValidator(2),MaxValueValidator(100000)])
    security_activity_multiplier=models.PositiveIntegerField(default=4,validators=[MinValueValidator(2),MaxValueValidator(100)])
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    max_questions = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(100)])
    max_options = models.PositiveIntegerField(default=6, validators=[MinValueValidator(2), MaxValueValidator(100)])
    allow_open_questions = models.BooleanField(default=True)
    vote_requires_auth = models.BooleanField(default=False)
    login_attempts = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    lockout_seconds = models.PositiveIntegerField(default=300, validators=[MinValueValidator(30), MaxValueValidator(86400)])
    session_seconds = models.PositiveIntegerField(default=1800, validators=[MinValueValidator(60), MaxValueValidator(86400)])
    retention_days = models.PositiveIntegerField(default=90, validators=[MinValueValidator(1)])
    default_validity_days = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1)])
    portal_url = models.URLField(blank=True)
    email_notifications = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name='singleton_settings')]

    @classmethod
    def current(cls):
        return cls.objects.get_or_create(pk=1)[0]
