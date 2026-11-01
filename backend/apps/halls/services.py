"""
Services for hall discovery, filtering, and recommendation scoring.
"""
from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from apps.common.utils import calculate_distance_km
from .models import Hall, HallAvailability


class RecommendationEngine:
    """
    Personalized ranking engine calculating match scores (0-100)
    with detailed explainability based on customer preference weights.
    """

    @classmethod
    def calculate_hall_score(
        cls,
        hall: Hall,
        preferences: Any | None = None,
        criteria: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate weighted score and explanations for a hall.
        """
        criteria = criteria or {}

        # Default weights (0-100)
        weight_budget = getattr(preferences, 'weight_budget', 30) if preferences else 30
        weight_capacity = getattr(preferences, 'weight_capacity', 20) if preferences else 20
        weight_proximity = getattr(preferences, 'weight_proximity', 20) if preferences else 20
        weight_amenities = getattr(preferences, 'weight_amenities', 15) if preferences else 15
        weight_rating = getattr(preferences, 'weight_rating', 15) if preferences else 15

        total_weight = weight_budget + weight_capacity + weight_proximity + weight_amenities + weight_rating
        if total_weight == 0:
            total_weight = 100

        reasons: list[str] = []

        # 1. Budget Score (0.0 to 1.0)
        customer_budget = criteria.get('budget_max') or (preferences.budget_max if preferences else None)
        hall_price = float(hall.base_price_per_day)

        if customer_budget:
            customer_budget_float = float(customer_budget)
            if hall_price <= customer_budget_float:
                budget_ratio = hall_price / customer_budget_float
                # Perfect score if within budget, slight bonus for good value
                budget_score = 1.0 - (0.2 * budget_ratio)
                savings = customer_budget_float - hall_price
                if savings > 0:
                    reasons.append(f"Within your budget of ₹{int(customer_budget_float):,} (saves ₹{int(savings):,})")
                else:
                    reasons.append(f"Fits within your budget of ₹{int(customer_budget_float):,}")
            else:
                over_ratio = (hall_price - customer_budget_float) / customer_budget_float
                budget_score = max(0.0, 1.0 - (over_ratio * 1.5))
        else:
            budget_score = 0.8
            reasons.append(f"Competitive pricing at ₹{int(hall_price):,}/day")

        # 2. Capacity Score (0.0 to 1.0)
        guest_count = criteria.get('guest_count') or (preferences.preferred_capacity if preferences else None)
        if guest_count:
            guest_count = int(guest_count)
            if hall.capacity_min <= guest_count <= hall.capacity_max:
                capacity_score = 1.0
                reasons.append(f"Ideal capacity for your {guest_count} guests (seats {hall.capacity_min}–{hall.capacity_max})")
            elif guest_count < hall.capacity_min:
                diff = hall.capacity_min - guest_count
                capacity_score = max(0.3, 1.0 - (diff / max(1, hall.capacity_min)))
            else:
                diff = guest_count - hall.capacity_max
                capacity_score = max(0.0, 1.0 - (diff / max(1, hall.capacity_max)))
        else:
            capacity_score = 0.85
            reasons.append(f"Accommodates up to {hall.capacity_max} guests")

        # 3. Proximity / City Score
        city = (criteria.get('city') or (preferences.preferred_city if preferences else '')).strip().lower()
        if city:
            if hall.location.city.lower() == city:
                proximity_score = 1.0
                reasons.append(f"Prime location in {hall.location.city} ({hall.location.name})")
            else:
                proximity_score = 0.2
        else:
            proximity_score = 0.8

        # 4. Amenities Match
        amenity_ids = criteria.get('amenity_ids', [])
        hall_amenity_ids = set(hall.amenities.values_list('id', flat=True))
        if amenity_ids:
            matches = len(set(amenity_ids).intersection(hall_amenity_ids))
            amenities_score = matches / len(amenity_ids)
            if matches > 0:
                reasons.append(f"Matches {matches} of {len(amenity_ids)} selected amenities")
        else:
            amenity_count = hall.amenities.count()
            amenities_score = min(1.0, 0.5 + (amenity_count * 0.1))
            if amenity_count > 0:
                reasons.append(f"Equipped with {amenity_count} amenities (AC, Parking, Power Backup)")

        # 5. Rating Score (Bayesian average: C=5, m=4.0)
        # Prevents halls with 1 five-star review outranking established 4.8-star halls
        C = 5.0
        m = 4.0
        n = float(hall.review_count)
        R = float(hall.avg_rating)
        bayesian_rating = ((C * m) + (n * R)) / (C + n)
        rating_score = min(1.0, bayesian_rating / 5.0)

        if hall.avg_rating > 0:
            reasons.append(f"Rated {hall.avg_rating}★ based on {hall.review_count} customer reviews")

        # Aggregate weighted score (0 to 100)
        raw_score = (
            (budget_score * weight_budget)
            + (capacity_score * weight_capacity)
            + (proximity_score * weight_proximity)
            + (amenities_score * weight_amenities)
            + (rating_score * weight_rating)
        ) / total_weight

        final_score = int(round(raw_score * 100))
        final_score = max(10, min(99, final_score))

        return {
            'match_score': final_score,
            'match_reasons': reasons[:4],
            'score_breakdown': {
                'budget': round(budget_score * 100),
                'capacity': round(capacity_score * 100),
                'proximity': round(proximity_score * 100),
                'amenities': round(amenities_score * 100),
                'rating': round(rating_score * 100),
            },
        }

