from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.utils import timezone
from apps.accounts.models import Grant
from apps.accounts.permissions import role_code
from apps.catalogs.models import Category
from .models import Content, Publication


def allowed_categories(user, operation='view'):
    if not user.is_authenticated or not user.is_active or not user.authorized:
        return Category.objects.none()
    if role_code(user) in ('admin','superadmin'):
        return Category.objects.all()
    grants = Grant.objects.filter(Q(user=user)|Q(role_id=user.role_id),operation=operation)
    return user.categories.filter(pk__in=grants.values('category_id'))


def content_queryset():
    return Content.objects.filter(deleted_at__isnull=True).select_related(
        'category','author','live_publication','news__area','event__area','service__area','service__service_type','survey'
    ).prefetch_related('survey__questions__options')


def visible_publications(at=None, limited=True):
    now = at or timezone.now()
    qs = Publication.objects.filter(content__live_publication_id=F('pk'),
        content__deleted_at__isnull=True,content__manual_active=True,
        category__active=True,category__visible=True,starts_at__lte=now
    ).filter(Q(ends_at__isnull=True)|Q(ends_at__gt=now)).select_related('category','content')
    if limited:
        ranked = qs.annotate(priority=Window(RowNumber(),partition_by=[F('category_id')],
            order_by=[F('starts_at').desc(),F('content_id').desc()])).filter(priority__lte=F('category__max_visible'))
        qs=Publication.objects.filter(pk__in=ranked.values('pk')).select_related('category','content')
    return qs.order_by('-starts_at','-content_id')


def is_public(content):
    return visible_publications().filter(content_id=content.pk).exists()


def public_data(publication):
    return dict(publication.data,version=publication.version,category_slug=publication.category.slug)


def operation_map(user):
    if role_code(user) in ('admin','superadmin'):
        return None
    assigned=set(user.categories.values_list('pk',flat=True))
    mapping={}
    for category,operation in Grant.objects.filter(Q(user=user)|Q(role_id=user.role_id)).values_list('category_id','operation'):
        if category in assigned: mapping.setdefault(category,set()).add(operation)
    return mapping
