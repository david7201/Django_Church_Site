from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from church.models import (
    Announcement,
    ConstructionMilestone,
    ConstructionUpdate,
    DonationMethod,
    FundraisingCampaign,
    GivingTier,
    Page,
    PageBlock,
    PageSection,
    ServiceTime,
    SiteSettings,
    STATUS_PUBLISHED,
)
from church.page_blocks import PAGE_BLOCK_DEFAULTS


class Command(BaseCommand):
    help = "Create starter content for the Mount Zion website."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Create starter content only when the site has no pages.",
        )

    def handle(self, *args, **options):
        if options["if_empty"] and Page.objects.filter(slug="home").exists():
            if options.get("verbosity", 1) > 0:
                self.stdout.write("Existing website content was left unchanged.")
            return

        self.create_settings()
        self.create_pages()
        self.create_service_times()
        self.create_fundraising()
        self.create_donations()
        self.create_announcements()
        self.create_page_blocks()
        if options.get("verbosity", 1) > 0:
            self.stdout.write(self.style.SUCCESS("Mount Zion starter content is ready."))

    def create_settings(self):
        settings = SiteSettings.load()
        settings.church_name = "Mount Zion"
        settings.tagline_en = "Romanian Pentecostal Church"
        settings.tagline_ro = "Biserica Penticostală Română"
        settings.default_meta_title_en = "Mount Zion Church"
        settings.default_meta_title_ro = "Biserica Mount Zion"
        settings.default_meta_description_en = "Mount Zion is a Romanian Pentecostal church in Dunshaughlin, Ireland."
        settings.default_meta_description_ro = "Mount Zion este o biserică penticostală română în Dunshaughlin, Irlanda."
        settings.footer_text_en = "Copyright Mount Zion Church"
        settings.footer_text_ro = "Copyright Biserica Mount Zion"
        settings.hero_image_static = "logo/mt2.jpeg"
        settings.scripture_reference_en = "Micah 4:5"
        settings.scripture_reference_ro = "Mica 4:5"
        settings.scripture_text_en = (
            "For all people will walk every one in the name of his god, and we will walk "
            "in the name of the Lord our God for ever and ever."
        )
        settings.scripture_text_ro = (
            "„Pe când toate popoarele umblă fiecare în numele dumnezeului său, noi vom umbla "
            "în Numele Domnului, Dumnezeului nostru, totdeauna şi în veci de veci!”"
        )
        settings.address = 'THE ROMANIAN PENTECOSTAL CHURCH "MOUNT ZION"\nGROWTOWN DUNSHAUGHLIN\nCO. MEATH\nA85 WY11'
        settings.email = "mountziondublin@gmail.com"
        settings.phone = "+353 089 452 4148"
        settings.directions_url = "https://www.google.com/maps/dir/?api=1&destination=GROWTOWN+DUNSHAUGHLIN%2C+A85+WY11"
        settings.show_construction_popup = True
        settings.construction_popup_title_en = "Church Building Update"
        settings.construction_popup_title_ro = "Actualizare despre construcția bisericii"
        settings.construction_popup_body_en = "Our church is currently under construction. Services are being held at a different location."
        settings.construction_popup_body_ro = "Biserica noastră este în construcție. Serviciile au loc temporar într-o altă locație."
        settings.construction_popup_button_en = "Go to Current Church"
        settings.construction_popup_button_ro = "Mergi la locația actuală"
        settings.current_church_url = "https://maps.app.goo.gl/1Qcd51AxkUctyZXP8"
        settings.save()

    def upsert_page(self, slug, **defaults):
        page, _ = Page.objects.update_or_create(slug=slug, defaults=defaults)
        return page

    def create_pages(self):
        home = self.upsert_page(
            "home",
            nav_title_en="Home",
            nav_title_ro="Acasă",
            hero_title_en="Mount Zion",
            hero_title_ro="Muntele Sion",
            hero_subtitle_en="Romanian Pentecostal Church",
            hero_subtitle_ro="Biserica Penticostală Română",
            hero_button_text_en="About us",
            hero_button_text_ro="Despre noi",
            hero_button_url="/about/",
            meta_title_en="Mount Zion",
            meta_title_ro="Muntele Sion",
            meta_description_en="Romanian Pentecostal Church in Dunshaughlin, Ireland.",
            meta_description_ro="Biserica Penticostală Română în Dunshaughlin, Irlanda.",
            navigation_order=0,
            show_in_navigation=False,
        )
        about = self.upsert_page(
            "about",
            nav_title_en="About",
            nav_title_ro="Despre noi",
            hero_title_en="About Us",
            hero_title_ro="Despre noi",
            hero_subtitle_en="View what our organization has achieved thus far",
            hero_subtitle_ro="Află mai multe despre misiunea și valorile noastre",
            hero_button_text_en="Our Mission",
            hero_button_text_ro="Misiunea noastră",
            hero_button_url="#mission",
            meta_title_en="About - Mount Zion Church",
            meta_title_ro="Despre noi - Biserica Mount Zion",
            meta_description_en="Learn about Mount Zion Church, our mission, vision and core values.",
            meta_description_ro="Află despre Biserica Mount Zion, misiunea, viziunea și valorile noastre.",
            navigation_order=30,
        )
        self.upsert_page(
            "services",
            nav_title_en="Services",
            nav_title_ro="Servicii",
            hero_title_en="Services",
            hero_title_ro="Servicii",
            hero_subtitle_en="Join us for worship, prayer, youth and Sunday services.",
            hero_subtitle_ro="Vino alături de noi la închinare, rugăciune, tineret și servicii de duminică.",
            meta_title_en="Services - Mount Zion Church",
            meta_title_ro="Servicii - Biserica Mount Zion",
            meta_description_en="Service times and worship information for Mount Zion Church.",
            meta_description_ro="Programul serviciilor și informații despre închinare la Biserica Mount Zion.",
            navigation_order=20,
        )
        charity = self.upsert_page(
            "charity",
            nav_title_en="Charity",
            nav_title_ro="Caritate",
            hero_title_en="Charity",
            hero_title_ro="Caritate",
            hero_subtitle_en="View what our charity organization has achieved thus far",
            hero_subtitle_ro="Vezi lucrarea noastră de caritate și impactul în comunitate",
            hero_button_text_en="Donate",
            hero_button_text_ro="Donează",
            hero_button_url="#donations",
            meta_title_en="Charity - Mount Zion Church",
            meta_title_ro="Caritate - Biserica Mount Zion",
            meta_description_en="Support Mount Zion Church charity work and community outreach.",
            meta_description_ro="Susține lucrarea de caritate și implicarea comunitară a Bisericii Mount Zion.",
            navigation_order=40,
        )
        self.upsert_page(
            "building",
            nav_title_en="Building Fund",
            nav_title_ro="Fondul de construcție",
            hero_title_en="New Church Building",
            hero_title_ro="Noua clădire a bisericii",
            hero_subtitle_en="Help us build a permanent home for worship and community.",
            hero_subtitle_ro="Ajută-ne să construim o casă permanentă pentru închinare și comunitate.",
            hero_button_text_en="Support the Build",
            hero_button_text_ro="Susține construcția",
            hero_button_url="#donations",
            meta_title_en="Building Fund - Mount Zion Church",
            meta_title_ro="Fondul de construcție - Biserica Mount Zion",
            meta_description_en="Follow progress and support the new Mount Zion church building.",
            meta_description_ro="Urmărește progresul și susține noua clădire a Bisericii Mount Zion.",
            navigation_order=50,
        )
        self.upsert_page(
            "events",
            nav_title_en="Events",
            nav_title_ro="Evenimente",
            hero_title_en="Events",
            hero_title_ro="Evenimente",
            hero_subtitle_en="Church activities, charity work and photo updates.",
            hero_subtitle_ro="Activități ale bisericii, lucrare de caritate și actualizări foto.",
            meta_title_en="Events - Mount Zion Church",
            meta_title_ro="Evenimente - Biserica Mount Zion",
            meta_description_en="See Mount Zion Church events, projects and photo slideshows.",
            meta_description_ro="Vezi evenimentele, proiectele și galeriile foto ale Bisericii Mount Zion.",
            navigation_order=60,
        )
        contact = self.upsert_page(
            "contact",
            nav_title_en="Contact",
            nav_title_ro="Contact",
            hero_title_en="Contact Us",
            hero_title_ro="Contactează-ne",
            hero_subtitle_en="View below for details",
            hero_subtitle_ro="Vezi detaliile mai jos",
            meta_title_en="Contact - Mount Zion Church",
            meta_title_ro="Contact - Biserica Mount Zion",
            meta_description_en="Contact Mount Zion Church in Dunshaughlin, Ireland.",
            meta_description_ro="Contactează Biserica Mount Zion din Dunshaughlin, Irlanda.",
            navigation_order=70,
        )
        self.upsert_page(
            "member-updates",
            nav_title_en="Member Updates",
            nav_title_ro="Actualiz\u0103ri pentru membri",
            hero_title_en="Member Updates",
            hero_title_ro="Actualiz\u0103ri pentru membri",
            hero_subtitle_en="Private announcements and updates for signed-in users",
            hero_subtitle_ro="Anun\u021buri \u015fi nout\u0103\u021bi private pentru utilizatorii autentifica\u021bi",
            meta_title_en="Member Updates - Mount Zion Church",
            meta_title_ro="Actualiz\u0103ri pentru membri - Biserica Mount Zion",
            meta_description_en="Private Mount Zion announcements and building updates for signed-in members.",
            meta_description_ro="Anun\u021buri \u015fi actualiz\u0103ri private Mount Zion pentru membrii autentifica\u021bi.",
            navigation_order=80,
            show_in_navigation=False,
        )

        section_data = [
            (home, "about-home", "About Mount Zion Church", "Despre Biserica Mount Zion", "Mount Zion Church is a community-driven church dedicated to spreading the gospel, fostering spiritual growth, and helping those in need through charitable works. Located in Dunshaughlin, Ireland, we welcome individuals and families to join us in worship, service, and community-building.\n\nWe are passionate about empowering communities in Romania and beyond, offering assistance through charity projects, support programs, and spiritual guidance. Our mission is to uplift lives by sharing love, hope, and the message of Christ.", "Biserica Mount Zion este o biserică orientată spre comunitate, dedicată răspândirii Evangheliei, creșterii spirituale și ajutorării celor în nevoie prin lucrări de caritate. Situată în Dunshaughlin, Irlanda, primim cu drag persoane și familii la închinare, slujire și părtășie.\n\nSuntem pasionați de sprijinirea comunităților din România și de pretutindeni, oferind ajutor, programe de susținere și călăuzire spirituală. Misiunea noastră este să ridicăm vieți prin dragoste, speranță și mesajul lui Hristos.", "dark_band", 10, "/charity/", "Support Us", "Susține-ne"),
            (about, "about-us", "About Us", "Despre noi", "Mount Zion Church is a vibrant, community-driven church that welcomes everyone with open arms. We are dedicated to spreading the teachings of Jesus Christ, offering hope and spiritual growth to all who come through our doors. Located in Dunshaughlin, Ireland, our church is more than just a place of worship; it is a supportive family and a beacon of light for those seeking comfort and truth.", "Biserica Mount Zion este o comunitate vie, care primește pe fiecare cu brațele deschise. Suntem dedicați răspândirii învățăturilor lui Isus Hristos și dorim să oferim speranță și creștere spirituală tuturor celor care ne trec pragul.", "text_card", 10, "", "", ""),
            (about, "vision", "Our Vision", "Viziunea noastră", "At Mount Zion Church, our vision is to create a welcoming environment for all, where people can experience the transformative power of Jesus Christ.", "Viziunea noastră este să creăm un loc primitor pentru toți, unde oamenii pot experimenta puterea transformatoare a lui Isus Hristos.", "text_card", 20, "", "", ""),
            (about, "mission", "Our Mission", "Misiunea noastră", "Our mission is to spread the message of love, hope, and redemption, and to support those in need through active charitable work and community outreach.", "Misiunea noastră este să răspândim mesajul dragostei, speranței și răscumpărării și să sprijinim pe cei în nevoie prin lucrare de caritate și implicare în comunitate.", "text_card", 30, "", "", ""),
            (about, "faith", "Faith", "Credință", "We believe in the transformative power of faith in Jesus Christ, and we encourage everyone to grow in their relationship with God.", "Credem în puterea transformatoare a credinței în Isus Hristos și încurajăm pe fiecare să crească în relația cu Dumnezeu.", "value_card", 40, "", "", ""),
            (about, "community", "Community", "Comunitate", "We foster a strong sense of community by supporting one another, serving together, and building meaningful relationships.", "Cultivăm o comunitate puternică prin sprijin reciproc, slujire împreună și relații pline de sens.", "value_card", 50, "", "", ""),
            (about, "charity-value", "Charity", "Caritate", "We are committed to giving back, helping those in need through charity projects, and creating a lasting positive impact in Romania and beyond.", "Suntem dedicați ajutorării celor în nevoie prin proiecte de caritate și printr-un impact pozitiv în România și dincolo de ea.", "value_card", 60, "", "", ""),
            (charity, "charity-work", "Charity Work", "Lucrare de caritate", "Empowering Communities, Sharing Hope: Our mission extends beyond the walls of our church. We are committed to bringing lasting change to communities in Romania, providing support, resources, and love to those who need it most. Together, we can uplift lives and make a difference.", "Întărim comunități și împărtășim speranță: misiunea noastră trece dincolo de zidurile bisericii. Dorim să aducem schimbare durabilă în comunități din România, oferind sprijin, resurse și dragoste celor care au cea mai mare nevoie.", "text_card", 10, "", "", ""),
            (charity, "charity-details", "Our Charity", "Caritatea noastră", "Charity Number: CHY 18466\nOrganisation Name: Mount Zion Church\nLocation: Ireland\nPurpose: Supporting vulnerable communities and families in need in Romania.", "Număr caritabil: CHY 18466\nNumele organizației: Biserica Mount Zion\nLocație: Irlanda\nScop: Sprijinirea comunităților vulnerabile și a familiilor în nevoie din România.", "text_card", 30, "", "", ""),
            (contact, "contact-intro", "We would love to hear from you", "Ne-ar plăcea să ne contactezi", "Use the contact form for general questions, or send a prayer request to the church team.", "Folosește formularul de contact pentru întrebări generale sau trimite o cerere de rugăciune echipei bisericii.", "text_card", 10, "", "", ""),
        ]

        for page, slug, title, title_ro, body, body_ro, layout, order, button_url, button_text, button_text_ro in section_data:
            PageSection.objects.update_or_create(
                page=page,
                title_en=title,
                defaults={
                    "title_ro": title_ro,
                    "body_en": body,
                    "body_ro": body_ro,
                    "layout": layout,
                    "order": order,
                    "button_url": button_url,
                    "button_text_en": button_text,
                    "button_text_ro": button_text_ro,
                    "status": STATUS_PUBLISHED,
                    "publish_at": timezone.now(),
                },
            )

    def create_page_blocks(self):
        settings = SiteSettings.load()
        visibility_fields = {
            ("home", "construction_popup"): "show_construction_popup",
            ("home", "scripture"): "show_home_scripture",
            ("home", "service_schedule"): "show_home_service_schedule",
            ("home", "fundraising"): "show_home_fundraising",
            ("home", "latest_update"): "show_home_latest_update",
            ("home", "team"): "show_home_team",
            ("home", "newsletter"): "show_home_newsletter",
            ("home", "home_address"): "show_home_contact_details",
            ("home", "home_email"): "show_home_contact_details",
            ("home", "home_phone"): "show_home_contact_details",
            ("charity", "donations"): "show_charity_donations",
            ("building", "fundraising"): "show_building_fundraising",
            ("building", "giving_tiers"): "show_building_giving_tiers",
            ("building", "milestones"): "show_building_milestones",
            ("building", "updates"): "show_building_updates",
            ("events", "events_listing"): "show_events_listing",
            ("contact", "contact_address"): "show_contact_details",
            ("contact", "contact_email"): "show_contact_details",
            ("contact", "contact_phone"): "show_contact_details",
            ("contact", "contact_form"): "show_contact_forms",
            ("contact", "prayer_form"): "show_contact_forms",
        }
        for page_slug, block_defaults in PAGE_BLOCK_DEFAULTS.items():
            page = Page.objects.get(slug=page_slug)
            for defaults in block_defaults:
                block_data = defaults.copy()
                key = block_data.pop("key")
                visibility_field = visibility_fields.get((page_slug, key))
                if visibility_field:
                    block_data["is_visible"] = getattr(settings, visibility_field)
                if page_slug == "home" and key == "construction_popup":
                    block_data.update(
                        {
                            "title_en": settings.construction_popup_title_en,
                            "title_ro": settings.construction_popup_title_ro,
                            "body_en": settings.construction_popup_body_en,
                            "body_ro": settings.construction_popup_body_ro,
                            "button_text_en": settings.construction_popup_button_en,
                            "button_text_ro": settings.construction_popup_button_ro,
                            "button_url": settings.current_church_url,
                        }
                    )
                PageBlock.objects.update_or_create(
                    page=page,
                    key=key,
                    defaults=block_data,
                )

    def create_service_times(self):
        rows = [
            (1, "Monday", "Luni", "Youth Service", "Serviciu de tineret", "20:00 - 22:00", False),
            (2, "Tuesday", "Marți", "Prayer Service", "Serviciu de rugăciune", "20:00 - 22:00", False),
            (3, "Wednesday", "Miercuri", "", "", "", True),
            (4, "Thursday", "Joi", "", "", "", True),
            (5, "Friday", "Vineri", "Prayer Service", "Serviciu de rugăciune", "20:00 - 22:00", False),
            (6, "Saturday", "Sâmbătă", "", "", "", True),
            (7, "Sunday", "Duminică", "Morning Service 9:00 - 12:00 | Evening Service", "Serviciu de dimineață 9:00 - 12:00 | Serviciu de seară", "18:00 - 20:00", False),
        ]
        for order, day, day_ro, name, name_ro, time_text, closed in rows:
            ServiceTime.objects.update_or_create(
                day_order=order,
                defaults={
                    "day_en": day,
                    "day_ro": day_ro,
                    "service_name_en": name,
                    "service_name_ro": name_ro,
                    "time_text": time_text,
                    "is_closed": closed,
                    "is_visible": True,
                },
            )

    def create_fundraising(self):
        campaign, _ = FundraisingCampaign.objects.update_or_create(
            is_primary=True,
            defaults={
                "title_en": "New Church Building Fund",
                "title_ro": "Fondul pentru noua clădire a bisericii",
                "description_en": "We are fundraising for the new church building so Mount Zion can have a permanent home for worship, prayer, youth gatherings and community outreach. Every gift helps move the project forward.",
                "description_ro": "Strângem fonduri pentru noua clădire a bisericii, pentru ca Mount Zion să aibă o casă permanentă pentru închinare, rugăciune, întâlniri de tineret și slujire în comunitate. Fiecare dar ajută proiectul să înainteze.",
                "goal_amount": Decimal("250000.00"),
                "raised_amount": Decimal("0.00"),
                "current_milestone_step": 2,
                "status": STATUS_PUBLISHED,
                "publish_at": timezone.now(),
            },
        )

        tiers = [
            ("Sponsor a Chair", "Sponsorizează un scaun", Decimal("50.00"), "Help provide seating for the new sanctuary.", "Ajută la asigurarea locurilor în noul sanctuar.", 10),
            ("Sponsor a Brick", "Sponsorizează o cărămidă", Decimal("100.00"), "Contribute directly to the physical building work.", "Contribuie direct la lucrarea fizică a construcției.", 20),
            ("Sponsor a Square Metre", "Sponsorizează un metru pătrat", Decimal("500.00"), "Support a larger part of the new church space.", "Susține o parte mai mare din noul spațiu al bisericii.", 30),
        ]
        for title, title_ro, amount, description, description_ro, order in tiers:
            GivingTier.objects.update_or_create(
                campaign=campaign,
                title_en=title,
                defaults={
                    "title_ro": title_ro,
                    "amount": amount,
                    "description_en": description,
                    "description_ro": description_ro,
                    "order": order,
                    "status": STATUS_PUBLISHED,
                    "publish_at": timezone.now(),
                },
            )

        milestones = [
            ("Planning and permissions", "Planificare și autorizații", "Project planning, permissions and preparation for the new church building.", "Planificarea proiectului, autorizațiile și pregătirea pentru noua clădire a bisericii.", 10, "done"),
            ("Foundation work", "Lucrări la fundație", "Groundwork and foundation preparation.", "Pregătirea terenului și a fundației.", 20, "in_progress"),
            ("Main structure", "Structura principală", "Walls, roof and main structural works.", "Pereți, acoperiș și lucrările structurale principale.", 30, "planned"),
            ("Interior and worship space", "Interiorul și spațiul de închinare", "Chairs, sound, lighting and final interior setup.", "Scaune, sunet, iluminat și amenajarea finală a interiorului.", 40, "planned"),
        ]
        for title, title_ro, description, description_ro, order, status in milestones:
            ConstructionMilestone.objects.update_or_create(
                campaign=campaign,
                title_en=title,
                defaults={
                    "title_ro": title_ro,
                    "description_en": description,
                    "description_ro": description_ro,
                    "order": order,
                    "milestone_status": status,
                    "status": STATUS_PUBLISHED,
                    "publish_at": timezone.now(),
                },
            )
        campaign.sync_milestone_statuses()

        ConstructionUpdate.objects.update_or_create(
            campaign=campaign,
            title_en="Building fund launched",
            defaults={
                "title_ro": "Fondul de construcție a fost lansat",
                "body_en": "We have opened the building fund page so the church family can follow progress and support the new church building.",
                "body_ro": "Am deschis pagina fondului de construcție pentru ca familia bisericii să poată urmări progresul și susține noua clădire.",
                "update_date": timezone.localdate(),
                "featured": True,
                "status": STATUS_PUBLISHED,
                "publish_at": timezone.now(),
            },
        )

    def create_donations(self):
        DonationMethod.objects.update_or_create(
            title_en="Bank Account Details",
            defaults={
                "method_type": "bank",
                "title_ro": "Detalii cont bancar",
                "description_en": "You can support our mission by bank transfer.",
                "description_ro": "Poți susține misiunea noastră prin transfer bancar.",
                "details": "Bank Name: AIB\nIBAN: IE61AIBK93239654732181\nSWIFT/BIK: AIBKIE2D\nAccount Number: 54732181\nN.S.C.: 92-23-96\nAccount Name: The Romanian Pentecostal Church Mount Zion CLG",
                "button_text_en": "Donate Online",
                "button_text_ro": "Donează online",
                "order": 10,
                "status": STATUS_PUBLISHED,
                "publish_at": timezone.now(),
            },
        )
        DonationMethod.objects.update_or_create(
            title_en="Donate with Tap2Tip",
            defaults={
                "method_type": "qr",
                "title_ro": "Donează cu Tap2Tip",
                "description_en": "You can also support our charity by scanning the QR code with your phone camera.",
                "description_ro": "Poți susține lucrarea noastră de caritate scanând codul QR cu telefonul.",
                "button_text_en": "Donate with Tap2Tip",
                "button_text_ro": "Donează cu Tap2Tip",
                "button_url": "https://tap2tip.io/tip/01KGHJAE502RMZSRH5Y7RWKSHY/432",
                "qr_image_static": "assets/img/QRCode_donations.jpeg",
                "order": 20,
                "status": STATUS_PUBLISHED,
                "publish_at": timezone.now(),
            },
        )

    def create_announcements(self):
        Announcement.objects.update_or_create(
            title_en="New church building updates are now available",
            defaults={
                "category": "building",
                "title_ro": "Actualizările despre noua clădire sunt disponibile",
                "body_en": "Follow the Building Fund page for timeline, giving tiers and photo updates.",
                "body_ro": "Urmărește pagina Fondului de construcție pentru etape, niveluri de donație și actualizări foto.",
                "is_urgent": True,
                "link_text_en": "View Building Fund",
                "link_text_ro": "Vezi fondul de construcție",
                "link_url": "/building-fund/",
                "status": STATUS_PUBLISHED,
                "publish_at": timezone.now(),
            },
        )
