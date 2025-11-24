from django.db import migrations
from django.core.management import call_command

def load_settings(apps, schema_editor):
    # Эта команда загрузит данные из вашего файла JSON в базу
    call_command('loaddata', 'initial_data.json')

class Migration(migrations.Migration):

    dependencies = [
        # Указываем зависимость от предыдущей миграции (Django сам подставит)
        ('shop', '0001_initial'),
        # ПРОВЕРЬТЕ: Если у вас последняя миграция не 0001,
        # посмотрите имя файла в папке migrations и впишите сюда последнее.
        # Обычно makemigrations сам ставит правильную зависимость,
        # если вы не удаляли содержимое dependencies при создании.
    ],

    operations = [
        migrations.RunPython(load_settings),
    ]