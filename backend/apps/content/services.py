from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.accounts.permissions import category_allowed, role_code
from apps.approvals.models import Approval
from apps.audit.models import record, AuditEvent
from apps.audit.context import audit_summary
from apps.notifications.models import Notification
from apps.notifications import services as notifications
from .models import Content, News, Event, Service, Survey, Question, Option, Publication
from .queries import visible_publications


def details_data(item):
    kind=item.category.content_type
    if kind=='news' and hasattr(item,'news'):
        d=item.news
        return {'area':d.area_id,'area_name':d.area.name,'external_url':d.external_url}
    if kind=='event' and hasattr(item,'event'):
        d=item.event
        return {'area':d.area_id,'area_name':d.area.name,'event_at':d.event_at.isoformat(),'contact':d.contact,'invitation_url':d.invitation_url}
    if kind=='service' and hasattr(item,'service'):
        d=item.service
        return {'area':d.area_id,'area_name':d.area.name if d.area_id else '', 'access_url':d.access_url,'service_type':d.service_type_id}
    if kind=='survey' and hasattr(item,'survey'):
        return {'external_url':item.survey.external_url,'questions':[
            {'id':q.pk,'text':q.text,'kind':q.kind,'required':q.required,'options':[{'id':o.pk,'text':o.text} for o in q.options.all()]}
            for q in item.survey.questions.all() if not q.archived]}
    return {}


def snapshot(item):
    return {'id':item.pk,'category':item.category_id,'category_slug':item.category.slug,'type':item.category.content_type,
        'title':item.title,'description':item.description,'starts_at':item.starts_at.isoformat(),
        'ends_at':item.ends_at.isoformat() if item.ends_at else None,'details':details_data(item),'extra_fields':item.extra_fields}


def publish(item, reviewer):
    version=Publication.objects.create(content=item,category=item.category,version=item.revision,
        data=snapshot(item),starts_at=item.starts_at,ends_at=item.ends_at,approved_by=reviewer)
    item.live_publication=version
    item.state=Content.State.APPROVED
    item.save(update_fields=['live_publication','state','updated_at'])
    return version


def save_details(item, data):
    kind=item.category.content_type
    model={'news':News,'event':Event,'service':Service}.get(kind)
    if model:
        model.objects.update_or_create(content=item,defaults=data)
    elif kind=='survey':
        questions=data.pop('questions')
        survey,_=Survey.objects.update_or_create(content=item,defaults=data)
        survey.questions.filter(archived=False).update(archived=True)
        for index,question in enumerate(questions):
            options=question.pop('options')
            q=Question.objects.create(survey=survey,position=index,**question)
            Option.objects.bulk_create([Option(question=q,**o) for o in options])


@transaction.atomic
def save_content(serializer, request):
    values=dict(serializer.validated_data)
    details=values.pop('details')
    item=serializer.instance
    prior=item.state if item else None
    before=audit_summary(item,values) if item else {}
    if item:
        Approval.objects.filter(content=item,state='pending').update(state='rejected',reason='Revisión sustituida por una edición.',reviewed_at=timezone.now())
        item.revision+=1
        for key,value in values.items(): setattr(item,key,value)
        item.state=Content.State.APPROVED if role_code(request.user) in ('admin','superadmin') and prior=='approved' else Content.State.DRAFT
        item.save()
    else:
        item=Content.objects.create(author=request.user,**values)
    save_details(item,details)
    # Clear reverse/prefetch caches after replacing survey definitions.
    item=Content.objects.select_related('category').get(pk=item.pk)
    if prior=='approved' and role_code(request.user) in ('admin','superadmin'):
        publish(item,request.user)
    record(request,'content.update' if serializer.instance else 'content.create',str(item.pk),
        {'version':item.revision,'fields':list(serializer.validated_data),'category':item.category_id,'before':before,'after':audit_summary(item,values)})
    return item


@transaction.atomic
def submit(item, request):
    Content.objects.select_for_update().get(pk=item.pk,deleted_at__isnull=True)
    item.refresh_from_db()
    if not category_allowed(request.user,item.category,'submit'):
        raise PermissionDenied('No tiene permiso para enviar esta categoría.')
    if item.state=='pending':
        return visible_publications(limited=False).filter(category=item.category).exclude(content_id=item.pk).count()>=item.category.max_visible
    if item.live_publication_id and item.live_publication.version==item.revision:
        raise ValidationError('Esta revisión ya está aprobada. Edite el contenido antes de reenviar.')
    approval=Approval.objects.create(content=item,requested_by=request.user,version=item.revision,proposal=snapshot(item))
    item.state='pending'; item.submitted_at=timezone.now()
    item.save(update_fields=['state','submitted_at','updated_at'])
    record(request,'content.submit',str(item.pk),{'version':item.revision})
    notifications.submitted(approval)
    visible=visible_publications(limited=False).filter(category=item.category).exclude(content_id=item.pk).count()
    return visible>=item.category.max_visible


@transaction.atomic
def review(item, request, approved, reason=''):
    if role_code(request.user) not in ('admin','superadmin'):
        raise PermissionDenied('Solo Admin/Superadmin puede revisar publicaciones.')
    Content.objects.select_for_update().get(pk=item.pk,deleted_at__isnull=True)
    item.refresh_from_db()
    approval=Approval.objects.filter(content=item,state='pending',version=item.revision).first()
    if not approval or item.state!='pending':
        previous=Approval.objects.filter(content=item,version=item.revision).order_by('-id').first()
        desired='approved' if approved else 'rejected'
        if previous and previous.state==desired and previous.reviewer_id==request.user.pk and previous.reason==reason:
            return
        raise ValidationError('No existe una solicitud pendiente para esta revisión.')
    if approval.requested_by_id==request.user.pk and role_code(request.user)=='gestor':
        raise PermissionDenied('Un Gestor no puede aprobar su propio contenido.')
    if not approved and not reason.strip():
        raise ValidationError({'reason':'Indique el motivo del rechazo.'})
    approval.state='approved' if approved else 'rejected'; approval.reason=reason
    approval.reviewer=request.user; approval.reviewed_at=timezone.now(); approval.save()
    if approved: publish(item,request.user)
    else:
        item.state='rejected'; item.save(update_fields=['state','updated_at'])
    record(request,'content.approve' if approved else 'content.reject',str(item.pk),{'version':item.revision,'approval':approval.pk})
    notifications.decided(approval)


@transaction.atomic
def register_expirations():
    now=timezone.now()
    count=0
    for publication in Publication.objects.select_for_update().filter(content__live_publication_id=F('pk'),
            content__deleted_at__isnull=True,ends_at__lte=now,expired_recorded_at__isnull=True).select_related('content'):
        publication.expired_recorded_at=now; publication.save(update_fields=['expired_recorded_at'])
        notifications.expired(publication)
        AuditEvent.objects.create(action='content.expired',entity='content',resource=str(publication.content_id),metadata={'publication':publication.pk})
        count+=1
    return count
