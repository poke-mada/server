# Generated by Django 5.1.5 on 2025-07-24 05:08

import django.db.models.deletion
from django.db import migrations, models


def declare_profile(apps, schema_editor):
    StreamerWildcardInventoryItem = apps.get_model("event_api", "StreamerWildcardInventoryItem")
    for item in StreamerWildcardInventoryItem.objects.all():
        item.profile = item.streamer.user.masters_profile
        item.save()


class Migration(migrations.Migration):
    dependencies = [
        ('event_api', '0052_errorlog_profile_wildcardlog_profile_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cointransaction',
            name='trainer',
        ),
        migrations.RemoveField(
            model_name='mastersprofile',
            name='custom_sprite',
        ),
        migrations.AddField(
            model_name='mastersprofile',
            name='streamer_name',
            field=models.CharField(default='', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='streamerwildcardinventoryitem',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='wildcard_inventory', to='event_api.mastersprofile'),
        ),
        migrations.AlterField(
            model_name='mastersprofile',
            name='tournament_league',
            field=models.CharField(
                choices=[('-', '------'), ('A', 'Liga A'), ('B', 'Liga B'), ('C', 'Liga C'), ('D', 'Liga D'),
                         ('E', 'Liga E')], default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='mastersprofile',
            name='web_picture',
            field=models.ImageField(null=True, upload_to='profiles/web/'),
        ),
        migrations.DeleteModel(
            name='StreamPlatformUrl',
        ),
        migrations.RunPython(
            declare_profile
        )
    ]
