'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Paginated } from '@/lib/types';

export interface VendorCategory {
  id: string;
  name: string;
  slug: string;
  icon: string;
}

export interface VendorProfile {
  id: string;
  business_name: string;
  category_name?: string;
  city: string;
  state: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  years_of_experience: number;
  avg_rating: string;
  review_count: number;
  is_verified: boolean;
  services: VendorService[];
}

export interface VendorService {
  id: string;
  category?: string;
  category_name?: string;
  title: string;
  description: string;
  base_price: string;
  pricing_unit: string;
  is_active: boolean;
}

export interface VendorServiceBooking {
  id: string;
  vendor_service: string;
  service_title: string;
  vendor_name: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  event_date: string;
  quoted_amount: string | null;
  status: 'enquiry' | 'quoted' | 'confirmed' | 'rejected' | 'completed';
  notes: string;
  created_at: string;
}

export function useVendorProfile() {
  return useQuery({
    queryKey: ['vendor-profile'],
    queryFn: () => api<VendorProfile>('/vendors/me/'),
  });
}

export function useUpdateVendorProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<VendorProfile>) =>
      api<VendorProfile>('/vendors/me/', { method: 'PATCH', body: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vendor-profile'] }),
  });
}

export function useVendorCategories() {
  return useQuery({
    queryKey: ['vendor-categories'],
    queryFn: () => api<VendorCategory[]>('/vendors/categories/'),
  });
}

export function useVendorServices() {
  return useQuery({
    queryKey: ['vendor-services'],
    queryFn: () => api<Paginated<VendorService>>('/vendors/services/'),
  });
}

export function useCreateVendorService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<VendorService>) =>
      api<VendorService>('/vendors/services/', { method: 'POST', body: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vendor-services'] }),
  });
}

export function useVendorBookings() {
  return useQuery({
    queryKey: ['vendor-bookings'],
    queryFn: () => api<Paginated<VendorServiceBooking>>('/vendors/bookings/'),
  });
}

export function useRespondVendorBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, quoted_amount }: { id: string; status?: string; quoted_amount?: string }) =>
      api<VendorServiceBooking>(`/vendors/bookings/${id}/respond/`, {
        method: 'POST',
        body: { status, quoted_amount },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vendor-bookings'] }),
  });
}

