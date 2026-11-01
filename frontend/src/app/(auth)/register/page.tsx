'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/form-field';
import { useRegister, type RegisterInput } from '@/hooks/use-auth';
import { ApiError, errorMessage } from '@/lib/api';
import { cn } from '@/lib/utils';

const ROLES: { value: RegisterInput['role']; title: string; body: string }[] = [
  { value: 'customer', title: 'I want to book halls', body: 'Find, compare and book halls for your events.' },
  { value: 'vendor', title: 'I provide event services', body: 'Catering, décor, photography, DJs and more.' },
];

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();
  const [form, setForm] = useState<RegisterInput>({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'customer',
  });
  const fieldErrors = register.error instanceof ApiError ? register.error.fieldErrors : {};

  function set<K extends keyof RegisterInput>(key: K, value: RegisterInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate(
      { ...form, phone: form.phone || undefined },
      {
        onSuccess: () => {
          router.push('/dashboard');
          router.refresh();
        },
      },
    );
  }

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Create your account</CardTitle>
        <CardDescription>
          Hall owners: sign up here first, then set up your organisation from the dashboard.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit} noValidate>
        <CardContent className="space-y-4">
          {register.isError ? <Alert variant="destructive">{errorMessage(register.error)}</Alert> : null}

          <fieldset className="grid gap-3 sm:grid-cols-2">
            <legend className="sr-only">Account type</legend>
            {ROLES.map((r) => (
              <label
                key={r.value}
                className={cn(
                  'cursor-pointer rounded-lg border p-4 text-sm transition-colors',
                  form.role === r.value ? 'border-primary bg-accent' : 'hover:bg-muted',
                )}
              >
                <input type="radio" name="role" value={r.value} checked={form.role === r.value} onChange={() => set('role', r.value)} className="sr-only" />
                <span className="block font-medium">{r.title}</span>
                <span className="mt-1 block text-muted-foreground">{r.body}</span>
              </label>
            ))}
          </fieldset>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField id="first_name" label="First name" error={fieldErrors.first_name}>
              <Input autoComplete="given-name" required value={form.first_name} onChange={(e) => set('first_name', e.target.value)} />
            </FormField>
            <FormField id="last_name" label="Last name" error={fieldErrors.last_name}>
              <Input autoComplete="family-name" required value={form.last_name} onChange={(e) => set('last_name', e.target.value)} />
            </FormField>
          </div>
          <FormField id="email" label="Email" error={fieldErrors.email}>
            <Input type="email" autoComplete="email" required value={form.email} onChange={(e) => set('email', e.target.value)} />
          </FormField>
          <FormField id="phone" label="Mobile (optional)" error={fieldErrors.phone} hint="10-digit Indian mobile number">
            <Input type="tel" autoComplete="tel" inputMode="tel" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
          </FormField>
          <FormField id="password" label="Password" error={fieldErrors.password} hint="At least 8 characters; not too common or similar to your name.">
            <Input type="password" autoComplete="new-password" required value={form.password} onChange={(e) => set('password', e.target.value)} />
          </FormField>
          <FormField id="password_confirm" label="Confirm password" error={fieldErrors.password_confirm}>
            <Input type="password" autoComplete="new-password" required value={form.password_confirm} onChange={(e) => set('password_confirm', e.target.value)} />
          </FormField>
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={register.isPending}>
            {register.isPending ? 'Creating account…' : 'Create account'}
          </Button>
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
