'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/form-field';
import { useRequestPasswordReset } from '@/hooks/use-auth';
import { errorMessage } from '@/lib/api';

export default function ForgotPasswordPage() {
  const reset = useRequestPasswordReset();
  const [email, setEmail] = useState('');

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Reset your password</CardTitle>
        <CardDescription>We&apos;ll email you a link to choose a new password.</CardDescription>
      </CardHeader>
      {reset.isSuccess ? (
        <CardContent>
          <Alert variant="success">{reset.data.detail}</Alert>
        </CardContent>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            reset.mutate(email);
          }}
        >
          <CardContent className="space-y-4">
            {reset.isError ? <Alert variant="destructive">{errorMessage(reset.error)}</Alert> : null}
            <FormField id="email" label="Email">
              <Input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </FormField>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={reset.isPending}>
              {reset.isPending ? 'Sending…' : 'Send reset link'}
            </Button>
          </CardFooter>
        </form>
      )}
      <CardFooter>
        <Link href="/login" className="text-sm text-primary hover:underline">
          Back to sign in
        </Link>
      </CardFooter>
    </Card>
  );
}
