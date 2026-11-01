'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/states';
import { useMe, useResendVerification } from '@/hooks/use-auth';

/** Shell for signed-in pages: loads the user and nudges email verification. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading } = useMe();
  const resend = useResendVerification();
  const router = useRouter();

  // Session expired or revoked (the proxy cleared the cookies): back to login.
  useEffect(() => {
    if (!isLoading && user === null) router.replace('/login');
  }, [isLoading, user, router]);

  if (isLoading || !user) return <Spinner />;

  return (
    <div className="container py-8">
      {user && !user.is_email_verified ? (
        <Alert variant="info" className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>Please verify your email address ({user.email}) to secure your account.</span>
          <Button size="sm" variant="outline" onClick={() => resend.mutate()} disabled={resend.isPending || resend.isSuccess}>
            {resend.isSuccess ? 'Email sent' : resend.isPending ? 'Sending…' : 'Resend email'}
          </Button>
        </Alert>
      ) : null}
      {children}
    </div>
  );
}
