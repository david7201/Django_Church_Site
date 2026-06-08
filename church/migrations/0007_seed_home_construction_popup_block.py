from django.db import migrations


def seed_home_construction_popup(apps, schema_editor):
    Page = apps.get_model("church", "Page")
    PageBlock = apps.get_model("church", "PageBlock")
    SiteSettings = apps.get_model("church", "SiteSettings")

    page = Page.objects.filter(slug="home").first()
    if not page:
        return
    settings = SiteSettings.objects.filter(pk=1).first()
    defaults = {
        "label": "Construction popup",
        "title_en": "Church Building Update",
        "title_ro": "Actualizare despre construc\u021bia bisericii",
        "body_en": "Our church is currently under construction. Services are being held at a different location.",
        "body_ro": "Biserica noastr\u0103 este \u00een construc\u021bie. Serviciile au loc temporar \u00eentr-o alt\u0103 loca\u021bie.",
        "button_text_en": "Go to Current Church",
        "button_text_ro": "Mergi la loca\u021bia actual\u0103",
        "button_url": "https://maps.app.goo.gl/1Qcd51AxkUctyZXP8",
        "order": 0,
        "is_visible": True,
    }
    if settings:
        defaults.update(
            {
                "title_en": settings.construction_popup_title_en,
                "title_ro": settings.construction_popup_title_ro,
                "body_en": settings.construction_popup_body_en,
                "body_ro": settings.construction_popup_body_ro,
                "button_text_en": settings.construction_popup_button_en,
                "button_text_ro": settings.construction_popup_button_ro,
                "button_url": settings.current_church_url,
                "is_visible": settings.show_construction_popup,
            }
        )
    PageBlock.objects.update_or_create(page=page, key="construction_popup", defaults=defaults)


def remove_home_construction_popup(apps, schema_editor):
    PageBlock = apps.get_model("church", "PageBlock")
    PageBlock.objects.filter(page__slug="home", key="construction_popup").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("church", "0006_event_show_description_event_show_gallery_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_home_construction_popup, remove_home_construction_popup),
    ]
