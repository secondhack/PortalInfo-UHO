from django.db import migrations


def preserve(apps,schema_editor):
    Content=apps.get_model('content','Content')
    Publication=apps.get_model('content','Publication')
    for item in Content.objects.filter(state='approved',live_publication__isnull=True).select_related('category'):
        kind=item.category.content_type
        details={}
        if kind in ('news','event','service'):
            Model=apps.get_model('content',{'news':'News','event':'Event','service':'Service'}[kind])
            specific=Model.objects.filter(content_id=item.pk).first()
            if specific:
                details={'area':specific.area_id,'area_name':specific.area.name if specific.area_id else ''}
                names={'news':['external_url'],'event':['event_at','contact','invitation_url'],'service':['access_url','service_type_id']}[kind]
                for name in names:
                    value=getattr(specific,name)
                    details[name]=value.isoformat() if hasattr(value,'isoformat') else value
        elif kind=='survey':
            Survey=apps.get_model('content','Survey'); survey=Survey.objects.filter(pk=item.pk).first()
            if survey:
                details={'external_url':survey.external_url,'questions':[{'id':q.pk,'text':q.text,'kind':q.kind,'required':q.required,
                    'options':list(q.options.values('id','text'))} for q in survey.questions.all()]}
        data={'id':item.pk,'category':item.category_id,'category_slug':item.category.slug,'type':kind,'title':item.title,
            'description':item.description,'starts_at':item.starts_at.isoformat(),'ends_at':item.ends_at.isoformat() if item.ends_at else None,
            'details':details,'extra_fields':item.extra_fields}
        p=Publication.objects.create(content_id=item.pk,category_id=item.category_id,version=item.revision,data=data,
            starts_at=item.starts_at,ends_at=item.ends_at,approved_by_id=None)
        item.live_publication_id=p.pk; item.save(update_fields=['live_publication'])


class Migration(migrations.Migration):
    dependencies=[('content','0002_publication_submission_and_more'),('catalogs','0003_builtin_content_types')]
    operations=[migrations.RunPython(preserve,migrations.RunPython.noop)]
