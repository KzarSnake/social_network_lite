# Generated by Django 2.2.16 on 2022-05-14 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20220514_2124'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',), 'verbose_name': 'Запись', 'verbose_name_plural': 'Записи'},
        ),
        migrations.RemoveField(
            model_name='post',
            name='created',
        ),
    ]