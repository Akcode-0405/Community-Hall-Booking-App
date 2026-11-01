/**
 * API types.
 *
 * Auth/profile/preferences types mirror the live Django serializers
 * (apps.accounts). Hall/booking types are the frontend's contract for the
 * Phase 3–4 endpoints listed in the architecture doc (§6.7, §6.8); the
 * backend serializers should match these shapes.
 */

export type UserRole =
  | 'platform_admin'
  | 'tenant_owner'
  | 'tenant_manager'
  | 'customer'
  | 'vendor';

export interface User {
  id: string;
  email: string;
  phone: string | null;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  avatar_url: string | null;
  city: string;
  state: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  email_notifications: boolean;
  sms_notifications: boolean;
  date_joined: string;
}

export interface CustomerPreference {
  id: string;
  user: string;
  preferred_city: string;
  preferred_state: string;
  budget_min: string | null;
  budget_max: string | null;
  preferred_capacity: number | null;
  preferred_hall_type: '' | 'indoor' | 'outdoor' | 'both';
  weight_budget: number;
  weight_capacity: number;
  weight_proximity: number;
  weight_amenities: number;
  weight_rating: number;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  count: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Standard error body produced by apps.common.exceptions. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown> | { errors: unknown[] };
  };
}

// ---------------------------------------------------------------------------
// Discovery & bookings (Phase 3–4 contract)
// ---------------------------------------------------------------------------

export type HallType = 'indoor' | 'outdoor' | 'both';

export interface HallSummary {
  id: string;
  name: string;
  city: string;
  state: string;
  locality: string;
  hall_type: HallType;
  capacity_min: number;
  capacity_max: number;
  starting_price: string | null;
  avg_rating: string | null;
  review_count: number;
  primary_photo_url: string | null;
  amenities: string[];
  distance_km?: number | null;
  /** Present on recommendation results: 0–100 match score + explanation. */
  match_score?: number;
  score_breakdown?: { factor: string; score: number; weight: number; reason: string }[];
}

export interface PricingRule {
  id: string;
  pricing_type: 'hourly' | 'half_day' | 'full_day' | 'custom';
  base_price: string;
  weekend_price: string | null;
}

export interface AdditionalCharge {
  id: string;
  name: string;
  amount: string;
  charge_type: 'fixed' | 'percentage';
  is_mandatory: boolean;
}

export interface HallDetail extends HallSummary {
  description: string;
  address_line_1: string;
  address_line_2: string;
  pin_code: string;
  latitude: number | null;
  longitude: number | null;
  photos: { id: string; url: string; caption: string }[];
  pricing: PricingRule[];
  additional_charges: AdditionalCharge[];
  taxes: { tax_name: string; tax_percentage: string; is_inclusive: boolean }[];
  seating: { arrangement_name: string; capacity: number }[];
  event_types: string[];
  cancellation_policy: string;
}

export type BookingStatus =
  | 'enquiry'
  | 'pending'
  | 'confirmed'
  | 'rejected'
  | 'cancelled'
  | 'completed';

export interface Booking {
  id: string;
  booking_number: string;
  hall: { id: string; name: string; city: string };
  event_date: string;
  start_time: string;
  end_time: string;
  guest_count: number;
  status: BookingStatus;
  total_amount: string;
  created_at: string;
}

export interface BookingRequest {
  hall: string;
  event_date: string;
  start_time: string;
  end_time: string;
  guest_count: number;
  special_requests?: string;
}
