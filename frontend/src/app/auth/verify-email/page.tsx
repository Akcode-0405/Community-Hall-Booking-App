'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useVerifyEmail } from '@/hooks/use-auth';
import { errorMessage } from '@/lib/api';

/** Landing page for the emailed link: /auth/verify-email?uid=…&token=… */
function Verify() {
  const params = useSearchParams();
  const uid = params.get('uid') ?? '';
  const token = params.get('token') ?? '';
  const verify = useVerifyEmail();
  const sent = useRef(false);

  useEffect(() => {
    // Guard against React strict-mode double effects.
    if (uid && token && !sent.current) {
      sent.current = true;
      verify.mutate({ uid, token });
    }
  }, [uid, token, verify]);

  if (!uid || !token) return <Alert variant="destructive">This verification link is incomplete.</Alert>;
  if (verify.isError) return <Alert variant="destructive">{errorMessage(verify.error)}</Alert>;
  if (verify.isSuccess) {
    return (
      <div className="space-y-4">
        <Alert variant="success">Your email address is verified.</Alert>
        <Button asChild className="w-full">
          <Link href="/dashboard">Go to dashboard</Link>
        </Button>
      </div>
    );
  }
  return <Spinner label="Verifying your email…" />;
}

export default function VerifyEmailPage() {
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
      </CardHeader>
      <CardContent>
        <Suspense fallback={<Spinner />}>
          <Verify />
        </Suspense>
      </CardContent>
    </Card>
  );
}
