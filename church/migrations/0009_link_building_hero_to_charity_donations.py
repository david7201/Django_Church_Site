from django.db import migrations


def update_building_button(apps, schema_editor):
    Page = apps.get_model("church", "Page")
    Page.objects.filter(
        slug="building",
        hero_button_url="#donations",
    ).update(hero_button_url="/charity/#donations")


def restore_building_button(apps, schema_editor):
    Page = apps.get_model("church", "Page")
    Page.objects.filter(
        slug="building",
        hero_button_url="/charity/#donations",
    ).update(hero_button_url="#donations")


class Migration(migrations.Migration):
    dependencies = [
        ("church", "0008_contactmessage_replied_at_contactmessage_replied_by_and_more"),
    ]

    operations = [
        migrations.RunPython(update_building_button, restore_building_button),
    ]
