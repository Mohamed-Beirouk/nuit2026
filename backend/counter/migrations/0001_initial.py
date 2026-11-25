from django.db import migrations, models


def seed_counter(apps, schema_editor):
    Counter = apps.get_model("counter", "Counter")
    Counter.objects.get_or_create(pk=1, defaults={"value": 0})


def remove_counter(apps, schema_editor):
    Counter = apps.get_model("counter", "Counter")
    Counter.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Counter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("value", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Claim",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=80)),
                ("number", models.PositiveIntegerField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["number"],
            },
        ),
        migrations.RunPython(seed_counter, remove_counter),
    ]
