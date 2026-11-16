from django.db import migrations


def freeze(apps,schema_editor):
    Approval=apps.get_model('approvals','Approval')
    Publication=apps.get_model('content','Publication')
    for approval in Approval.objects.filter(proposal={}).select_related('content__category').iterator(chunk_size=100):
        item=approval.content
        version=Publication.objects.filter(content_id=item.pk,version=approval.version).first()
        if version:approval.proposal=version.data
        elif item.revision==approval.version:
            kind=item.category.content_type;details={}
            if kind in ['news','event','service']:
                model=apps.get_model('content',{'news':'News','event':'Event','service':'Service'}[kind])
                specific=model.objects.filter(content_id=item.pk).first()
                if specific:
                    details={'area':specific.area_id,'area_name':specific.area.name if specific.area_id else ''}
                    names={'news':['external_url'],'event':['event_at','contact','invitation_url'],'service':['access_url','service_type_id']}[kind]
                    for name in names:
                        value=getattr(specific,name);details[name]=value.isoformat() if hasattr(value,'isoformat') else value
            if kind=='survey':
                survey=apps.get_model('content','Survey').objects.filter(pk=item.pk).first()
                if survey:details={'external_url':survey.external_url,'questions':[{'id':q.pk,'text':q.text,'kind':q.kind,'required':q.required,'options':list(q.options.values('id','text'))} for q in survey.questions.filter(archived=False)]}
            approval.proposal={'id':item.pk,'category':item.category_id,'category_slug':item.category.slug,'type':kind,
                'title':item.title,'description':item.description,'starts_at':item.starts_at.isoformat(),
                'ends_at':item.ends_at.isoformat() if item.ends_at else None,'details':details,'extra_fields':item.extra_fields}
        if approval.proposal:approval.save(update_fields=['proposal'])


class Migration(migrations.Migration):
    dependencies=[('approvals','0003_approval_proposal'),('content','0004_submission_demo_submission_seed_key')]
    operations=[migrations.RunPython(freeze,migrations.RunPython.noop)]
