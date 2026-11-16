from django.db import migrations


def entities(apps,schema_editor):
    Model=apps.get_model('audit','AuditEvent')
    for item in Model.objects.filter(entity='').iterator(chunk_size=500):
        item.entity=item.action.split('.')[0][:50];item.save(update_fields=['entity'])


class Migration(migrations.Migration):
    dependencies=[('audit','0002_auditevent_entity')]
    operations=[migrations.RunPython(entities,migrations.RunPython.noop)]
