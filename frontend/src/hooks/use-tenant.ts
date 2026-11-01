'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Paginated } from '@/lib/types';

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  subdomain: string;
  business_type: string;
  email: string;
  phone: string;
  city: string;
  state: string;
  pin_code: string;
  gstin: string;
  status: 'active' | 'suspended' | 'trial' | 'expired';
  suspension_reason: string;
  suspension_note: string;
  hall_count: number;
  manager_count: number;
  created_at: string;
}

export interface TenantLocation {
  id: string;
  name: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state: string;
  pin_code: string;
  hall_count: number;
  is_active: boolean;
}

export function useAllTenants() {
  return useQuery({
    queryKey: ['tenants', 'all'],
    queryFn: () => api<Paginated<Tenant>>('/tenants/'),
  });
}

export function useCurrentTenant() {
  return useQuery({
    queryKey: ['tenants', 'current'],
    queryFn: () => api<Tenant>('/tenants/current/'),
  });
}

export function useSuspendTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) =>
      api<Tenant>(`/tenants/${id}/suspend/`, { method: 'POST', body: { note } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  });
}

export function useActivateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api<Tenant>(`/tenants/${id}/activate/`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  });
}

export function useTenantHalls() {
  return useQuery({
    queryKey: ['tenant-halls'],
    queryFn: () => api<Paginated<any>>('/halls/manage/halls/'),
  });
}

export function useCreateTenantHall() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) =>
      api<any>('/halls/manage/halls/', { method: 'POST', body: data }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tenant-halls'] });
      qc.invalidateQueries({ queryKey: ['halls'] });
    },
  });
}

export function useTenantLocations() {
  return useQuery({
    queryKey: ['tenant-locations'],
    queryFn: () => api<Paginated<TenantLocation>>('/halls/manage/locations/'),
  });
}

export function useCreateTenantLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<TenantLocation>) =>
      api<TenantLocation>('/halls/manage/locations/', { method: 'POST', body: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-locations'] }),
  });
}

export function useApproveBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      api<any>(`/bookings/${id}/approve/`, { method: 'POST', body: { notes } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  });
}

export function useRejectBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      api<any>(`/bookings/${id}/reject/`, { method: 'POST', body: { reason } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  });
}

