from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_service_last_error"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="last_modified_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="service",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=False,
        ),
    ]