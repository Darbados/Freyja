from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0004_freyjauser_email_confirmed_at")]

    operations = [
        migrations.AddField(
            model_name="freyjauser",
            name="totp_secret",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="freyjauser",
            name="two_factor_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
