'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/form-field';
import { useConfirmPasswordReset } from '@/hooks/use-auth';
import { ApiError, errorMessage } from '@/lib/api';

/** Landing page for the emailed link: /auth/reset-password?uid=…&token=… */
function ResetForm() {
  const params = useSearchParams();
  const uid = params.get('uid') ?? '';
  const token = params.get('token') ?? '';
  const confirm = useConfirmPasswordReset();
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const fieldErrors = confirm.error instanceof ApiError ? confirm.error.fieldErrors : {};

  if (!uid || !token) {
    return <Alert variant="destructive">This reset link is incomplete. Please request a new one.</Alert>;
  }

  if (confirm.isSuccess) {
    return (
      <div className="space-y-4">
        <Alert variant="success">Your password has been reset.</Alert>
        <Button asChild className="w-full">
          <Link href="/login">Sign in</Link>
        </Button>
      </div>
    );
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        confirm.mutate({ uid, token, new_password: password, new_password_confirm: passwordConfirm });
      }}
    >
      {confirm.isError ? <Alert variant="destructive">{errorMessage(confirm.error)}</Alert> : null}
      <FormField id="new_password" label="New password" error={fieldErrors.new_password}>
        <Input type="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
      </FormField>
      <FormField id="new_password_confirm" label="Confirm new password" error={fieldErrors.new_password_confirm}>
        <Input type="password" autoComplete="new-password" required value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} />
      </FormField>
      <Button type="submit" className="w-full" disabled={confirm.isPending}>
        {confirm.isPending ? 'Saving…' : 'Set new password'}
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Choose a new password</CardTitle>
      </CardHeader>
      <CardContent>
        <Suspense>
          <ResetForm />
        </Suspense>
      </CardContent>
      <CardFooter>
        <Link href="/forgot-password" className="text-sm text-primary hover:underline">
          Request a new link
        </Link>
      </CardFooter>
    </Card>
  );
}
