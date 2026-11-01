'use client';

import { useEffect, useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/form-field';
import { Spinner } from '@/components/states';
import { useChangePassword, useMe, useUpdateProfile, type ProfileUpdate } from '@/hooks/use-auth';
import { ApiError, errorMessage } from '@/lib/api';
import { formatDate, ROLE_LABELS } from '@/lib/utils';

function ProfileForm() {
  const { data: user } = useMe();
  const update = useUpdateProfile();
  const [form, setForm] = useState<ProfileUpdate>({});
  const fieldErrors = update.error instanceof ApiError ? update.error.fieldErrors : {};

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone ?? '',
        city: user.city,
        state: user.state,
        email_notifications: user.email_notifications,
        sms_notifications: user.sms_notifications,
      });
    }
  }, [user]);

  if (!user) return <Spinner />;

  const set = <K extends keyof ProfileUpdate>(k: K, v: ProfileUpdate[K]) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2">
          {user.email}
          <Badge variant={user.is_email_verified ? 'success' : 'secondary'}>{user.is_email_verified ? 'Verified' : 'Unverified'}</Badge>
          <Badge variant="outline">{ROLE_LABELS[user.role]}</Badge>
          <span>· Member since {formatDate(user.date_joined)}</span>
        </CardDescription>
      </CardHeader>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          update.mutate({ ...form, phone: form.phone || null });
        }}
      >
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {update.isSuccess ? <Alert variant="success" className="sm:col-span-2">Profile saved.</Alert> : null}
          {update.isError ? (
            <Alert variant="destructive" className="sm:col-span-2">{errorMessage(update.error)}</Alert>
          ) : null}
          <FormField id="first_name" label="First name" error={fieldErrors.first_name}>
            <Input value={form.first_name ?? ''} onChange={(e) => set('first_name', e.target.value)} />
          </FormField>
          <FormField id="last_name" label="Last name" error={fieldErrors.last_name}>
            <Input value={form.last_name ?? ''} onChange={(e) => set('last_name', e.target.value)} />
          </FormField>
          <FormField id="phone" label="Mobile" error={fieldErrors.phone}>
            <Input type="tel" value={form.phone ?? ''} onChange={(e) => set('phone', e.target.value)} />
          </FormField>
          <FormField id="city" label="City" error={fieldErrors.city}>
            <Input value={form.city ?? ''} onChange={(e) => set('city', e.target.value)} />
          </FormField>
          <FormField id="state" label="State" error={fieldErrors.state}>
            <Input value={form.state ?? ''} onChange={(e) => set('state', e.target.value)} />
          </FormField>
          <fieldset className="space-y-2 sm:col-span-2">
            <legend className="text-sm font-medium">Notifications</legend>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="h-4 w-4" checked={Boolean(form.email_notifications)} onChange={(e) => set('email_notifications', e.target.checked)} />
              Email notifications
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="h-4 w-4" checked={Boolean(form.sms_notifications)} onChange={(e) => set('sms_notifications', e.target.checked)} />
              SMS notifications
            </label>
          </fieldset>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={update.isPending}>
            {update.isPending ? 'Saving…' : 'Save changes'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}

function ChangePasswordForm() {
  const change = useChangePassword();
  const [form, setForm] = useState({ old_password: '', new_password: '', new_password_confirm: '' });
  const fieldErrors = change.error instanceof ApiError ? change.error.fieldErrors : {};

  return (
    <Card>
      <CardHeader>
        <CardTitle>Change password</CardTitle>
      </CardHeader>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          change.mutate(form, { onSuccess: () => setForm({ old_password: '', new_password: '', new_password_confirm: '' }) });
        }}
      >
        <CardContent className="space-y-4">
          {change.isSuccess ? <Alert variant="success">Password changed.</Alert> : null}
          {change.isError ? <Alert variant="destructive">{errorMessage(change.error)}</Alert> : null}
          <FormField id="old_password" label="Current password" error={fieldErrors.old_password}>
            <Input type="password" autoComplete="current-password" value={form.old_password} onChange={(e) => setForm({ ...form, old_password: e.target.value })} />
          </FormField>
          <FormField id="new_password" label="New password" error={fieldErrors.new_password}>
            <Input type="password" autoComplete="new-password" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
          </FormField>
          <FormField id="new_password_confirm" label="Confirm new password" error={fieldErrors.new_password_confirm}>
            <Input type="password" autoComplete="new-password" value={form.new_password_confirm} onChange={(e) => setForm({ ...form, new_password_confirm: e.target.value })} />
          </FormField>
        </CardContent>
        <CardFooter>
          <Button type="submit" variant="outline" disabled={change.isPending}>
            {change.isPending ? 'Updating…' : 'Update password'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}

export default function ProfilePage() {
  return (
    <div className="mx-auto grid max-w-3xl gap-6">
      <h1 className="text-2xl font-bold tracking-tight">Account settings</h1>
      <ProfileForm />
      <ChangePasswordForm />
    </div>
  );
}
