'use client';

/**
 * Discovery & booking hooks.
 * Connects to Django REST API endpoints for hall discovery, filtering, and booking lifecycle.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Booking, BookingRequest, HallDetail, HallSummary, Paginated } from '@/lib/types';

export interface HallFilters {
  q?: string;
  city?: string;
  state?: string;
  event_date?: string;
  guests?: number;
  budget_max?: number;
  hall_type?: string;
  min_rating?: number;
  ordering?: string;
  page?: number;
}

export function useHallSearch(filters: HallFilters) {
  return useQuery({
    queryKey: ['halls', filters],
    queryFn: () =>
      api<Paginated<HallSummary>>('/discover/halls/', { params: filters }),
    placeholderData: (prev) => prev,
  });
}

export function useHall(id: string | undefined) {
  return useQuery({
    queryKey: ['hall', id],
    queryFn: () => api<HallDetail>(`/discover/halls/${id}/`),
    enabled: Boolean(id),
  });
}

export function useBookings(status?: string) {
  return useQuery({
    queryKey: ['bookings', status ?? 'all'],
    queryFn: () => api<Paginated<Booking>>('/bookings/', { params: { status } }),
  });
}

export function useCreateBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: BookingRequest) => api<Booking>('/bookings/', { method: 'POST', body: input }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  });
}

export function useCancelBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api<Booking>(`/bookings/${id}/cancel/`, { method: 'POST', body: { reason } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  });
}
