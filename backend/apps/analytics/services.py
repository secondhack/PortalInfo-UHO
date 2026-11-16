from dataclasses import dataclass
from django.db import transaction
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import ValidationError
from apps.audit.context import client_context
from apps.catalogs.models import Category
from apps.content.queries import visible_publications
from .models import AccessLog,ContentView


@dataclass(frozen=True)
class VerifiedPortalIdentity:
    """Input from a trusted server-side provider, never deserialized from HTTP JSON."""
    uid:str
    user_type:str


def identity_from(request,verified=None):
    if verified:
        if verified.user_type not in ['institucional','trabajadores','estudiantes']:
            raise ValueError('Unknown verified identity type')
        return 'u:'+salted_hmac('portal-identity',verified.uid).hexdigest(),verified.user_type
    from apps.portal.identity import visitor, pseudonym
    portal = visitor(request)
    if portal:
        return pseudonym(portal), 'demo_' + portal.user_type
    if request.user.is_authenticated and request.user.is_active and request.user.authorized:
        return 'cms:'+salted_hmac('portal-identity',str(request.user.pk)).hexdigest(),'demo' if request.user.demo else 'institucional'
    return '','anonymous'


@transaction.atomic
def record_activity(request,section,content_id=None,event_type='view',verified=None,demo=False,seed_key=None):
    category=None;content=None
    if content_id:
        publication=visible_publications().filter(content_id=content_id).first()
        if not publication or section!=publication.category.slug:
            raise ValidationError('El contenido no está visible o no corresponde a la sección.')
        content=publication.content;category=publication.category
    elif section not in ['portal','login']:
        category=Category.objects.filter(slug=section,active=True,visible=True).first()
        if not category:raise ValidationError('Sección no habilitada.')
    context=client_context(request)
    uid,user_type=identity_from(request,verified)
    log=AccessLog.objects.create(uid=uid,user_type=user_type,event_type=event_type,section=section,content=content,
        ip=context['ip'],user_agent=context['user_agent'],device=context['device'],demo=demo,seed_key=seed_key)
    if event_type=='view':
        ContentView.objects.create(access_log=log,category=category,content=content,section=section,
            ip=context['ip'],device=context['device'],uid=uid,user_type=user_type,demo=demo,seed_key=seed_key)
    return log
