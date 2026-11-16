from django.db import migrations


def assign_types(apps,schema_editor):
    Category=apps.get_model('catalogs','Category')
    for slug,kind in [('noticias','news'),('eventos','event'),('avisos','notice'),('servicios','service'),('encuestas','survey')]:
        Category.objects.filter(slug=slug,dynamic=False).update(content_type=kind)


class Migration(migrations.Migration):
    dependencies=[('catalogs','0002_category_content_type')]
    operations=[migrations.RunPython(assign_types,migrations.RunPython.noop)]
