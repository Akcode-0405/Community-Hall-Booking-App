"""
Management command to seed comprehensive, production-ready demo data for all 4 user roles:
1. Platform Admin (admin@hallbooking.com / AdminPass123!)
2. Tenant Owner (owner@grandpalace.com / OwnerPass123!) & Manager (manager@grandpalace.com / ManagerPass123!)
3. Customer (customer@example.com / CustomerPass123!)
4. Vendor (vendor@royaldecor.com / VendorPass123!)

Populates tenants, locations across India, halls with photos & pricing, amenities,
customer bookings in various states (pending, confirmed), and vendor service listings.
"""
from __future__ import annotations

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date

from apps.accounts.models import CustomerPreference, User, UserRole
from apps.tenants.models import Tenant, TenantMembership, TenantStatus, SuspensionReason
from apps.halls.models import Amenity, Hall, HallAvailability, HallReview, HallType, Location
from apps.bookings.models import Booking, BookingStatus, BookingStatusLog, EventType, SlotType
from apps.vendors.models import PricingUnit, VendorCategory, VendorProfile, VendorService, VendorServiceBooking


class Command(BaseCommand):
    help = "Seed demo data for all 4 roles (admin, tenant manager, customer, vendor)."

    def handle(self, *args, **options):
        self.stdout.write("Starting demo data seeding...")

        # ------------------------------------------------------------------
        # 1. Platform Admin
        # ------------------------------------------------------------------
        admin_user, created = User.objects.get_or_create(
            email="admin@hallbooking.com",
            defaults={
                "first_name": "SaaS",
                "last_name": "Admin",
                "role": UserRole.PLATFORM_ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "city": "Bengaluru",
                "state": "Karnataka",
            },
        )
        admin_user.set_password("AdminPass123!")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        self.stdout.write(self.style.SUCCESS(f"✔ Platform Admin: {admin_user.email}"))

        # ------------------------------------------------------------------
        # 2. Tenants (Hall-owning Businesses)
        # ------------------------------------------------------------------
        # Tenant A: Grand Palace (Active, Multi-location)
        t_grand, _ = Tenant.objects.get_or_create(
            slug="grand-palace",
            defaults={
                "name": "Grand Palace Conventions & Resorts",
                "contact_email": "contact@grandpalace.com",
                "contact_phone": "+919876500001",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560034",
                "status": TenantStatus.ACTIVE,
                "gstin": "29AAAAA0000A1Z5",
            },
        )

        # Tenant B: Royal Heritage (Active, Chennai & Hyderabad)
        t_royal, _ = Tenant.objects.get_or_create(
            slug="royal-heritage",
            defaults={
                "name": "Royal Heritage Mandapams",
                "contact_email": "contact@royalheritage.com",
                "contact_phone": "+919876500002",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "pin_code": "600017",
                "status": TenantStatus.ACTIVE,
                "gstin": "33BBBBB0000B1Z2",
            },
        )

        # Tenant C: CityLights (Suspended — perfect to show Admin suspension demo)
        t_citylights, _ = Tenant.objects.get_or_create(
            slug="citylights-banquets",
            defaults={
                "name": "CityLights Luxury Banquets",
                "contact_email": "hello@citylights.com",
                "contact_phone": "+919876500003",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pin_code": "400050",
                "status": TenantStatus.SUSPENDED,
                "suspension_reason": SuspensionReason.ADMIN,
                "suspension_note": "Awaiting KYC compliance verification.",
            },
        )

        # ------------------------------------------------------------------
        # 3. Tenant Owner & Manager Accounts
        # ------------------------------------------------------------------
        owner_user, _ = User.objects.get_or_create(
            email="owner@grandpalace.com",
            defaults={
                "first_name": "Vikram",
                "last_name": "Singhania",
                "role": UserRole.TENANT_OWNER,
                "city": "Bengaluru",
                "state": "Karnataka",
            },
        )
        owner_user.set_password("OwnerPass123!")
        owner_user.save()

        TenantMembership.objects.get_or_create(
            user=owner_user,
            tenant=t_grand,
            defaults={"role": "owner", "is_active": True},
        )

        manager_user, _ = User.objects.get_or_create(
            email="manager@grandpalace.com",
            defaults={
                "first_name": "Arun",
                "last_name": "Nair",
                "role": UserRole.TENANT_MANAGER,
                "city": "Bengaluru",
                "state": "Karnataka",
            },
        )
        manager_user.set_password("ManagerPass123!")
        manager_user.save()

        TenantMembership.objects.get_or_create(
            user=manager_user,
            tenant=t_grand,
            defaults={"role": "manager", "is_active": True},
        )
        self.stdout.write(self.style.SUCCESS(f"✔ Tenant Manager: {manager_user.email} (Tenant: {t_grand.name})"))

        # ------------------------------------------------------------------
        # 4. Customer Account
        # ------------------------------------------------------------------
        customer_user, _ = User.objects.get_or_create(
            email="customer@example.com",
            defaults={
                "first_name": "Rahul",
                "last_name": "Verma",
                "role": UserRole.CUSTOMER,
                "city": "Bengaluru",
                "state": "Karnataka",
                "phone": "+919876543210",
            },
        )
        customer_user.set_password("CustomerPass123!")
        customer_user.save()

        CustomerPreference.objects.update_or_create(
            user=customer_user,
            defaults={
                "preferred_city": "Bengaluru",
                "preferred_state": "Karnataka",
                "budget_min": Decimal("50000.00"),
                "budget_max": Decimal("150000.00"),
                "preferred_capacity": 300,
                "weight_budget": 35,
                "weight_capacity": 25,
                "weight_proximity": 20,
                "weight_amenities": 10,
                "weight_rating": 10,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✔ Customer: {customer_user.email}"))

        # ------------------------------------------------------------------
        # 5. Vendor Account
        # ------------------------------------------------------------------
        vendor_user, _ = User.objects.get_or_create(
            email="vendor@royaldecor.com",
            defaults={
                "first_name": "Pooja",
                "last_name": "Sharma",
                "role": UserRole.VENDOR,
                "city": "Bengaluru",
                "state": "Karnataka",
                "phone": "+919876599999",
            },
        )
        vendor_user.set_password("VendorPass123!")
        vendor_user.save()

        vendor_profile, _ = VendorProfile.objects.update_or_create(
            user=vendor_user,
            defaults={
                "business_name": "Royal Décor & Catering Services",
                "description": "Premium wedding styling, traditional floral mandaps, and authentic multi-cuisine catering across South India.",
                "city": "Bengaluru",
                "state": "Karnataka",
                "contact_email": "vendor@royaldecor.com",
                "contact_phone": "+919876599999",
                "is_verified": True,
                "avg_rating": Decimal("4.90"),
                "review_count": 28,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✔ Vendor: {vendor_user.email} ({vendor_profile.business_name})"))

        # ------------------------------------------------------------------
        # 6. Amenities
        # ------------------------------------------------------------------
        amenity_names = [
            ("Air Conditioning", "snowflake", "Climate"),
            ("Valet Parking", "car", "Parking"),
            ("Power Backup (100% DG)", "zap", "Utilities"),
            ("Dedicated Dining Hall", "utensils", "Dining"),
            ("Audio & Visual Sound System", "volume-2", "Entertainment"),
            ("Bridal Dressing Rooms", "sparkles", "Facilities"),
            ("High Speed Wi-Fi", "wifi", "Connectivity"),
            ("In-house Kitchen Facility", "chef-hat", "Dining"),
            ("Stage & Mandap Decor Setup", "flower2", "Decor"),
            ("CCTV Surveillance", "shield-check", "Security"),
            ("Wheelchair Accessible", "accessibility", "Facilities"),
            ("Alcohol Permitted (with license)", "wine", "Policy"),
        ]
        amenity_objs = {}
        for name, icon, cat in amenity_names:
            obj, _ = Amenity.objects.get_or_create(name=name, defaults={"icon": icon, "category": cat})
            amenity_objs[name] = obj

        # ------------------------------------------------------------------
        # 7. Locations & Halls
        # ------------------------------------------------------------------
        loc_blr_1, _ = Location.objects.get_or_create(
            tenant=t_grand,
            name="Grand Palace Koramangala",
            defaults={
                "address_line_1": "80 Feet Road, 4th Block, Koramangala",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560034",
                "latitude": Decimal("12.935200"),
                "longitude": Decimal("77.624500"),
            },
        )

        loc_blr_2, _ = Location.objects.get_or_create(
            tenant=t_grand,
            name="Grand Palace Whitefield",
            defaults={
                "address_line_1": "ITPB Main Road, Whitefield",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560066",
                "latitude": Decimal("12.969800"),
                "longitude": Decimal("77.749900"),
            },
        )

        loc_chn, _ = Location.objects.get_or_create(
            tenant=t_royal,
            name="Royal Heritage T. Nagar",
            defaults={
                "address_line_1": "G.N. Chetty Road, T. Nagar",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "pin_code": "600017",
                "latitude": Decimal("13.041800"),
                "longitude": Decimal("80.234100"),
            },
        )

        loc_mum, _ = Location.objects.get_or_create(
            tenant=t_citylights,
            name="CityLights Bandra",
            defaults={
                "address_line_1": "Hill Road, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pin_code": "400050",
                "latitude": Decimal("19.054400"),
                "longitude": Decimal("72.840200"),
            },
        )

        # Photo galleries (curated Unsplash wedding/event halls)
        photos_grand_ballroom = [
            "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1545232979-fbf68fe9f8a8?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?auto=format&fit=crop&w=1200&q=80",
        ]
        photos_crystal = [
            "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1520854221256-17451cc331bf?auto=format&fit=crop&w=1200&q=80",
        ]
        photos_lawn = [
            "https://images.unsplash.com/photo-1532712938310-34cb3982ef74?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=1200&q=80",
        ]
        photos_heritage = [
            "https://images.unsplash.com/photo-1587271407850-8d438ca9fdf2?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80",
        ]

        halls_data = [
            {
                "tenant": t_grand,
                "location": loc_blr_1,
                "name": "The Royal Grand Ballroom",
                "slug": "royal-grand-ballroom-koramangala",
                "description": "Lavish air-conditioned convention hall featuring Italian marble flooring, crystal chandeliers, acoustic ceiling, and separate dining space for up to 800 guests.",
                "capacity_min": 150,
                "capacity_max": 800,
                "hall_type": HallType.INDOOR,
                "base_price_per_day": Decimal("110000.00"),
                "base_price_per_hour": Decimal("12000.00"),
                "cleaning_fee": Decimal("3500.00"),
                "security_deposit": Decimal("25000.00"),
                "avg_rating": Decimal("4.85"),
                "review_count": 42,
                "photos": photos_grand_ballroom,
                "amenities": list(amenity_objs.values())[:10],
            },
            {
                "tenant": t_grand,
                "location": loc_blr_1,
                "name": "Crystal Banquet & Conference Hall",
                "slug": "crystal-banquet-koramangala",
                "description": "Elegant mid-sized banquet hall tailored for sangeet, ring ceremonies, corporate conferences and private celebrations.",
                "capacity_min": 50,
                "capacity_max": 300,
                "hall_type": HallType.INDOOR,
                "base_price_per_day": Decimal("65000.00"),
                "base_price_per_hour": Decimal("7500.00"),
                "cleaning_fee": Decimal("2000.00"),
                "security_deposit": Decimal("15000.00"),
                "avg_rating": Decimal("4.70"),
                "review_count": 29,
                "photos": photos_crystal,
                "amenities": list(amenity_objs.values())[:8],
            },
            {
                "tenant": t_grand,
                "location": loc_blr_2,
                "name": "Palace Lawn & Open Air Amphitheatre",
                "slug": "palace-lawn-whitefield",
                "description": "Sprawling 20,000 sq.ft. manicured green lawns with decorative fairy-light canopy, fountain backdrop, and dedicated buffet courts for grand receptions.",
                "capacity_min": 200,
                "capacity_max": 1500,
                "hall_type": HallType.BOTH,
                "base_price_per_day": Decimal("145000.00"),
                "base_price_per_hour": Decimal("16000.00"),
                "cleaning_fee": Decimal("5000.00"),
                "security_deposit": Decimal("30000.00"),
                "avg_rating": Decimal("4.92"),
                "review_count": 56,
                "photos": photos_lawn,
                "amenities": list(amenity_objs.values()),
            },
            {
                "tenant": t_royal,
                "location": loc_chn,
                "name": "Sanskriti Traditional Heritage Kalyana Mandapam",
                "slug": "sanskriti-heritage-mandapam-chennai",
                "description": "South Indian temple-architecture inspired wedding mandapam with teak wood carvings, pure brass lamp fittings, and seated banana-leaf dining hall for 400 people.",
                "capacity_min": 100,
                "capacity_max": 650,
                "hall_type": HallType.INDOOR,
                "base_price_per_day": Decimal("85000.00"),
                "base_price_per_hour": Decimal("9000.00"),
                "cleaning_fee": Decimal("3000.00"),
                "security_deposit": Decimal("20000.00"),
                "avg_rating": Decimal("4.80"),
                "review_count": 38,
                "photos": photos_heritage,
                "amenities": list(amenity_objs.values())[:9],
            },
            {
                "tenant": t_citylights,
                "location": loc_mum,
                "name": "CityLights Seaside Ballroom",
                "slug": "citylights-seaside-ballroom-bandra",
                "description": "Ultra-modern sea-view banquet hall in Bandra with panoramic glass facade, intelligent RGB lighting, and luxury VIP green rooms.",
                "capacity_min": 100,
                "capacity_max": 500,
                "hall_type": HallType.INDOOR,
                "base_price_per_day": Decimal("175000.00"),
                "base_price_per_hour": Decimal("20000.00"),
                "cleaning_fee": Decimal("5000.00"),
                "security_deposit": Decimal("40000.00"),
                "avg_rating": Decimal("4.65"),
                "review_count": 21,
                "photos": photos_grand_ballroom,
                "amenities": list(amenity_objs.values())[:10],
            },
        ]

        created_halls = []
        for h_data in halls_data:
            amenities = h_data.pop("amenities")
            hall_obj, _ = Hall.objects.update_or_create(
                slug=h_data["slug"],
                defaults=h_data,
            )
            hall_obj.amenities.set(amenities)
            created_halls.append(hall_obj)

        self.stdout.write(self.style.SUCCESS(f"✔ Created {len(created_halls)} halls across Bengaluru, Chennai, and Mumbai."))

        # ------------------------------------------------------------------
        # 8. Sample Customer Bookings
        # ------------------------------------------------------------------
        primary_hall = created_halls[0]  # Royal Grand Ballroom
        secondary_hall = created_halls[1]  # Crystal Banquet

        # Booking 1: Upcoming Confirmed Booking for Customer
        b1_date = timezone.now().date() + timedelta(days=21)
        b1, _ = Booking.objects.get_or_create(
            booking_number="BK-2026-VRM01",
            defaults={
                "tenant": t_grand,
                "hall": primary_hall,
                "customer": customer_user,
                "event_name": "Rahul & Sneha Wedding Reception",
                "event_type": EventType.RECEPTION,
                "event_date": b1_date,
                "slot_type": SlotType.FULL_DAY,
                "guest_count": 350,
                "status": BookingStatus.CONFIRMED,
                "base_amount": primary_hall.base_price_per_day,
                "additional_charges": primary_hall.cleaning_fee,
                "tax_amount": round((primary_hall.base_price_per_day + primary_hall.cleaning_fee) * Decimal("0.18"), 2),
                "total_amount": round((primary_hall.base_price_per_day + primary_hall.cleaning_fee) * Decimal("1.18"), 2),
                "confirmed_at": timezone.now() - timedelta(days=2),
                "special_requests": "Need stage setup completed by 10 AM. Valet driver team required.",
            },
        )
        BookingStatusLog.objects.get_or_create(
            booking=b1,
            to_status=BookingStatus.CONFIRMED,
            defaults={"from_status": BookingStatus.PENDING, "changed_by": manager_user, "notes": "Approved by manager."},
        )

        # Booking 2: Pending Approval Request (Manager can APPROVE/REJECT in demo!)
        b2_date = timezone.now().date() + timedelta(days=35)
        b2, _ = Booking.objects.get_or_create(
            booking_number="BK-2026-PEN02",
            defaults={
                "tenant": t_grand,
                "hall": secondary_hall,
                "customer": customer_user,
                "event_name": "Sangeet Night & Dance Sensation",
                "event_type": EventType.BIRTHDAY,
                "event_date": b2_date,
                "slot_type": SlotType.HALF_DAY_EVENING,
                "guest_count": 180,
                "status": BookingStatus.PENDING,
                "base_amount": secondary_hall.base_price_per_day,
                "additional_charges": secondary_hall.cleaning_fee,
                "tax_amount": round((secondary_hall.base_price_per_day + secondary_hall.cleaning_fee) * Decimal("0.18"), 2),
                "total_amount": round((secondary_hall.base_price_per_day + secondary_hall.cleaning_fee) * Decimal("1.18"), 2),
                "special_requests": "Looking for high bass sound system permission until 10:30 PM.",
            },
        )
        BookingStatusLog.objects.get_or_create(
            booking=b2,
            to_status=BookingStatus.PENDING,
            defaults={"from_status": "", "changed_by": customer_user, "notes": "Customer submitted booking request."},
        )

        # ------------------------------------------------------------------
        # 9. Vendor Service Categories & Listings
        # ------------------------------------------------------------------
        vcat_catering, _ = VendorCategory.objects.get_or_create(name="Catering & Feasts", defaults={"icon": "utensils"})
        vcat_decor, _ = VendorCategory.objects.get_or_create(name="Mandap & Floral Décor", defaults={"icon": "flower"})
        vcat_photo, _ = VendorCategory.objects.get_or_create(name="Photography & Film", defaults={"icon": "camera"})
        vcat_dj, _ = VendorCategory.objects.get_or_create(name="DJ, Sound & Lights", defaults={"icon": "music"})

        s1, _ = VendorService.objects.get_or_create(
            vendor=vendor_profile,
            category=vcat_decor,
            title="Royal Mandap & Floral Entrance Package",
            defaults={
                "description": "Exquisite fresh floral mandap (jasmine, roses, orchids), 100ft red carpet entrance, stage backdrop with LED lighting and photobooth.",
                "price_from": Decimal("45000.00"),
                "price_to": Decimal("85000.00"),
                "pricing_unit": PricingUnit.PER_EVENT,
                "is_active": True,
            },
        )

        s2, _ = VendorService.objects.get_or_create(
            vendor=vendor_profile,
            category=vcat_catering,
            title="Grand South & North Indian Multi-Cuisine Buffet",
            defaults={
                "description": "Welcome mocktails, 4 live counters (chaat, dosa, pasta), 8 main course specialties, traditional sweets and ice cream counter.",
                "price_from": Decimal("750.00"),
                "price_to": Decimal("1200.00"),
                "pricing_unit": PricingUnit.PER_PLATE,
                "is_active": True,
            },
        )

        s3, _ = VendorService.objects.get_or_create(
            vendor=vendor_profile,
            category=vcat_photo,
            title="Candid Wedding Photography & 4K Cinematic Film",
            defaults={
                "description": "2 candid photographers, 2 traditional videographers, drone cinematography, 40-page luxury photo album and teaser video.",
                "price_from": Decimal("60000.00"),
                "price_to": Decimal("120000.00"),
                "pricing_unit": PricingUnit.PER_EVENT,
                "is_active": True,
            },
        )

        # Customer enquiry to vendor
        VendorServiceBooking.objects.get_or_create(
            vendor_service=s1,
            customer=customer_user,
            event_date=b1_date,
            defaults={
                "status": "confirmed",
                "quoted_amount": Decimal("65000.00"),
                "notes": "Floral theme matching reception outfits (pastel pink & gold).",
            },
        )

        VendorServiceBooking.objects.get_or_create(
            vendor_service=s2,
            customer=customer_user,
            event_date=b2_date,
            defaults={
                "status": "enquiry",
                "quoted_amount": Decimal("0.00"),
                "notes": "Catering estimate requested for 180 guests evening dinner.",
            },
        )

        self.stdout.write(self.style.SUCCESS("✔ Created vendor services and customer service bookings."))

        # Reviews
        HallReview.objects.get_or_create(
            hall=primary_hall,
            customer=customer_user,
            defaults={
                "rating": 5,
                "title": "Breathtaking venue and impeccable staff!",
                "comment": "Hosted my brother's engagement here. The AC, valet parking and dining hall management made the entire evening seamless.",
            },
        )

        self.stdout.write(self.style.SUCCESS("\n🎉 DEMO SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write("---------------------------------------------------------------")
        self.stdout.write("DEMO ACCOUNTS READY TO TEST:")
        self.stdout.write("1. Platform Admin:  admin@hallbooking.com   / AdminPass123!")
        self.stdout.write("2. Tenant Manager:  manager@grandpalace.com / ManagerPass123!")
        self.stdout.write("   Tenant Owner:    owner@grandpalace.com   / OwnerPass123!")
        self.stdout.write("3. Customer:        customer@example.com    / CustomerPass123!")
        self.stdout.write("4. Vendor:          vendor@royaldecor.com   / VendorPass123!")
        self.stdout.write("---------------------------------------------------------------")
