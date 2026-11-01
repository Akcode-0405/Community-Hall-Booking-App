'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import type { CustomerPreference, User } from '@/lib/types';

export const meKey = ['me'] as const;

/** Current user, or null when signed out. */
export function useMe() {
  return useQuery<User | null>({
    queryKey: meKey,
    queryFn: async () => {
      try {
        return await api<User>('/auth/me/');
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null;
        throw err;
      }
    },
    staleTime: 60_000,
    retry: false,
  });
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: 'customer' | 'vendor';
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: LoginInput) => api<{ user: User }>('/login', { method: 'POST', body: input, base: '/api/auth' }),
    onSuccess: ({ user }) => qc.setQueryData(meKey, user),
  });
}

export function useRegister() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: RegisterInput) =>
      api<{ user: User }>('/register', { method: 'POST', body: input, base: '/api/auth' }),
    onSuccess: ({ user }) => qc.setQueryData(meKey, user),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  const router = useRouter();
  return useMutation({
    mutationFn: () => api<{ detail: string }>('/logout', { method: 'POST', base: '/api/auth' }),
    onSettled: () => {
      qc.clear();
      qc.setQueryData(meKey, null);
      router.push('/');
      router.refresh();
    },
  });
}

export type ProfileUpdate = Partial<
  Pick<User, 'first_name' | 'last_name' | 'phone' | 'avatar_url' | 'city' | 'state' | 'email_notifications' | 'sms_notifications'>
>;

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileUpdate) => api<User>('/auth/me/', { method: 'PATCH', body: input }),
    onSuccess: (user) => qc.setQueryData(meKey, user),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (input: { old_password: string; new_password: string; new_password_confirm: string }) =>
      api<{ detail: string }>('/auth/change-password/', { method: 'POST', body: input }),
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (email: string) => api<{ detail: string }>('/auth/password/reset/', { method: 'POST', body: { email } }),
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: (input: { uid: string; token: string; new_password: string; new_password_confirm: string }) =>
      api<{ detail: string }>('/auth/password/reset/confirm/', { method: 'POST', body: input }),
  });
}

export function useVerifyEmail() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { uid: string; token: string }) =>
      api<{ detail: string }>('/auth/verify-email/', { method: 'POST', body: input }),
    onSuccess: () => qc.invalidateQueries({ queryKey: meKey }),
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: () => api<{ detail: string }>('/auth/verify-email/resend/', { method: 'POST', body: {} }),
  });
}

export const preferencesKey = ['preferences'] as const;

export function usePreferences(enabled = true) {
  return useQuery({
    queryKey: preferencesKey,
    queryFn: () => api<CustomerPreference>('/auth/preferences/'),
    enabled,
  });
}

export function useUpdatePreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Partial<CustomerPreference>) =>
      api<CustomerPreference>('/auth/preferences/', { method: 'PATCH', body: input }),
    onSuccess: (prefs) => qc.setQueryData(preferencesKey, prefs),
  });
}
