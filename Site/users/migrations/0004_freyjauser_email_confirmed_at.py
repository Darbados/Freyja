from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_remove_freyjauser_manager"),
    ]

    operations = [
        migrations.AddField(
            model_name="freyjauser",
            name="email_confirmed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
