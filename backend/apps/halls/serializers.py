"""
Serializers for halls, locations, amenities, and discovery.
"""
from __future__ import annotations

from decimal import Decimal
from rest_framework import serializers

from .models import Amenity, Hall, HallAvailability, HallReview, Location
from .services import RecommendationEngine


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'category']


class LocationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    hall_count = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'name',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'pin_code',
            'latitude',
            'longitude',
            'is_active',
            'hall_count',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']

    def get_hall_count(self, obj: Location) -> int:
        return obj.halls.filter(is_active=True).count()


class HallListSerializer(serializers.ModelSerializer):
    """Card representation for hall discovery and listing matching HallSummary."""
    city = serializers.ReadOnlyField(source='location.city')
    state = serializers.ReadOnlyField(source='location.state')
    locality = serializers.ReadOnlyField(source='location.name')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    starting_price = serializers.SerializerMethodField()
    primary_photo_url = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    match_reasons = serializers.SerializerMethodField()
    score_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = Hall
        fields = [
            'id',
            'name',
            'slug',
            'city',
            'state',
            'locality',
            'hall_type',
            'capacity_min',
            'capacity_max',
            'starting_price',
            'avg_rating',
            'review_count',
            'primary_photo_url',
            'amenities',
            'distance_km',
            'match_score',
            'match_reasons',
            'score_breakdown',
            'tenant_name',
        ]

    def _get_engine_data(self, obj: Hall):
        request = self.context.get('request')
        user = request.user if request else None
        pref = getattr(user, 'preferences', None) if user and user.is_authenticated else None
        criteria = self.context.get('criteria', {})
        return RecommendationEngine.calculate_hall_score(obj, pref, criteria)

    def get_starting_price(self, obj: Hall) -> str:
        return str(obj.base_price_per_day)

    def get_primary_photo_url(self, obj: Hall) -> str | None:
        if obj.photos and len(obj.photos) > 0:
            p = obj.photos[0]
            return p if isinstance(p, str) else p.get('url')
        return None

    def get_amenities(self, obj: Hall) -> list[str]:
        return [a.name for a in obj.amenities.all()]

    def get_distance_km(self, obj: Hall) -> float | None:
        return None

    def get_match_score(self, obj: Hall) -> int:
        return self._get_engine_data(obj)['match_score']

    def get_match_reasons(self, obj: Hall) -> list[str]:
        return self._get_engine_data(obj)['match_reasons']

    def get_score_breakdown(self, obj: Hall):
        data = self._get_engine_data(obj)
        sb = data.get('score_breakdown', {})
        if isinstance(sb, list):
            return sb
        return [
            {'factor': 'Budget fit', 'score': sb.get('budget', 90), 'weight': 30, 'reason': 'Within budget range'},
            {'factor': 'Capacity fit', 'score': sb.get('capacity', 90), 'weight': 20, 'reason': 'Fits guest requirements'},
            {'factor': 'Proximity', 'score': sb.get('proximity', 85), 'weight': 20, 'reason': 'Accessible location'},
            {'factor': 'Amenities', 'score': sb.get('amenities', 95), 'weight': 15, 'reason': 'Key amenities present'},
            {'factor': 'Customer Rating', 'score': sb.get('rating', 90), 'weight': 15, 'reason': f'{obj.avg_rating}★ reviews'},
        ]


class HallReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.full_name')

    class Meta:
        model = HallReview
        fields = ['id', 'customer_name', 'rating', 'title', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class HallDetailSerializer(serializers.ModelSerializer):
    """Full detailed view of a hall matching HallDetail contract."""
    city = serializers.ReadOnlyField(source='location.city')
    state = serializers.ReadOnlyField(source='location.state')
    locality = serializers.ReadOnlyField(source='location.name')
    address_line_1 = serializers.ReadOnlyField(source='location.address_line_1')
    address_line_2 = serializers.ReadOnlyField(source='location.address_line_2')
    pin_code = serializers.ReadOnlyField(source='location.pin_code')
    latitude = serializers.ReadOnlyField(source='location.latitude')
    longitude = serializers.ReadOnlyField(source='location.longitude')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    starting_price = serializers.SerializerMethodField()
    primary_photo_url = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    match_reasons = serializers.SerializerMethodField()
    score_breakdown = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    additional_charges = serializers.SerializerMethodField()
    taxes = serializers.SerializerMethodField()
    seating = serializers.SerializerMethodField()
    event_types = serializers.SerializerMethodField()
    location = LocationSerializer(read_only=True)
    reviews = HallReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'city',
            'state',
            'locality',
            'address_line_1',
            'address_line_2',
            'pin_code',
            'latitude',
            'longitude',
            'hall_type',
            'capacity_min',
            'capacity_max',
            'starting_price',
            'avg_rating',
            'review_count',
            'primary_photo_url',
            'amenities',
            'distance_km',
            'match_score',
            'match_reasons',
            'score_breakdown',
            'photos',
            'pricing',
            'additional_charges',
            'taxes',
            'seating',
            'event_types',
            'cancellation_policy',
            'tenant',
            'tenant_name',
            'location',
            'reviews',
            'is_active',
            'is_published',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at']

    def _get_engine_data(self, obj: Hall):
        request = self.context.get('request')
        user = request.user if request else None
        pref = getattr(user, 'preferences', None) if user and user.is_authenticated else None
        return RecommendationEngine.calculate_hall_score(obj, pref, {})

    def get_starting_price(self, obj: Hall) -> str:
        return str(obj.base_price_per_day)

    def get_primary_photo_url(self, obj: Hall) -> str | None:
        if obj.photos and len(obj.photos) > 0:
            p = obj.photos[0]
            return p if isinstance(p, str) else p.get('url')
        return None

    def get_amenities(self, obj: Hall) -> list[str]:
        return [a.name for a in obj.amenities.all()]

    def get_distance_km(self, obj: Hall) -> float | None:
        return None

    def get_match_score(self, obj: Hall) -> int:
        return self._get_engine_data(obj)['match_score']

    def get_match_reasons(self, obj: Hall) -> list[str]:
        return self._get_engine_data(obj)['match_reasons']

    def get_score_breakdown(self, obj: Hall):
        data = self._get_engine_data(obj)
        sb = data.get('score_breakdown', {})
        if isinstance(sb, list):
            return sb
        return [
            {'factor': 'Budget fit', 'score': sb.get('budget', 90), 'weight': 30, 'reason': 'Within budget range'},
            {'factor': 'Capacity fit', 'score': sb.get('capacity', 90), 'weight': 20, 'reason': 'Fits guest requirements'},
            {'factor': 'Proximity', 'score': sb.get('proximity', 85), 'weight': 20, 'reason': 'Accessible location'},
            {'factor': 'Amenities', 'score': sb.get('amenities', 95), 'weight': 15, 'reason': 'Key amenities present'},
            {'factor': 'Customer Rating', 'score': sb.get('rating', 90), 'weight': 15, 'reason': f'{obj.avg_rating}★ reviews'},
        ]

    def get_photos(self, obj: Hall) -> list[dict]:
        if not obj.photos:
            return []
        photos = []
        for i, p in enumerate(obj.photos):
            url = p if isinstance(p, str) else p.get('url', '')
            photos.append({
                'id': f'photo-{i}',
                'url': url,
                'caption': obj.name,
            })
        return photos

    def get_pricing(self, obj: Hall) -> list[dict]:
        day = obj.base_price_per_day
        hour = obj.base_price_per_hour
        return [
            {
                'id': 'p-full',
                'pricing_type': 'full_day',
                'base_price': str(day),
                'weekend_price': str(int(day * Decimal('1.2'))),
            },
            {
                'id': 'p-half',
                'pricing_type': 'half_day',
                'base_price': str(int(day * Decimal('0.6'))),
                'weekend_price': str(int(day * Decimal('0.7'))),
            },
            {
                'id': 'p-hour',
                'pricing_type': 'hourly',
                'base_price': str(hour),
                'weekend_price': str(int(hour * Decimal('1.25'))),
            },
        ]

    def get_additional_charges(self, obj: Hall) -> list[dict]:
        return [
            {
                'id': 'ac-clean',
                'name': 'Cleaning Fee',
                'amount': str(obj.cleaning_fee),
                'charge_type': 'fixed',
                'is_mandatory': True,
            },
            {
                'id': 'ac-dep',
                'name': 'Refundable Security Deposit',
                'amount': str(obj.security_deposit),
                'charge_type': 'fixed',
                'is_mandatory': False,
            },
        ]

    def get_taxes(self, obj: Hall) -> list[dict]:
        return [
            {
                'tax_name': 'GST',
                'tax_percentage': str(obj.gst_percentage),
                'is_inclusive': False,
            }
        ]

    def get_seating(self, obj: Hall) -> list[dict]:
        return [
            {'arrangement_name': 'Floating / Reception', 'capacity': obj.capacity_max},
            {'arrangement_name': 'Theater Style', 'capacity': int(obj.capacity_max * 0.75)},
            {'arrangement_name': 'Banquet / Round Tables', 'capacity': int(obj.capacity_max * 0.5)},
        ]

    def get_event_types(self, obj: Hall) -> list[str]:
        return ['Wedding', 'Reception', 'Engagement', 'Birthday Party', 'Corporate Conference', 'Exhibition']


class HallCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer used by Tenant Managers/Owners to add or edit a hall."""
    amenity_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Amenity.objects.all(), source='amenities', required=False
    )

    class Meta:
        model = Hall
        fields = [
            'id',
            'location',
            'name',
            'description',
            'capacity_min',
            'capacity_max',
            'hall_type',
            'is_active',
            'is_published',
            'photos',
            'base_price_per_day',
            'base_price_per_hour',
            'cleaning_fee',
            'security_deposit',
            'gst_percentage',
            'cancellation_policy',
            'amenity_ids',
        ]
        read_only_fields = ['id']


class HallAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = HallAvailability
        fields = ['id', 'hall', 'date', 'is_available', 'reason']
        read_only_fields = ['id']
