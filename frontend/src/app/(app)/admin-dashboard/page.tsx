'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  CreditCard,
  ExternalLink,
  Power,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Users,
} from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Spinner } from '@/components/states';
import { useMe } from '@/hooks/use-auth';
import { useActivateTenant, useAllTenants, useSuspendTenant } from '@/hooks/use-tenant';
import { errorMessage } from '@/lib/api';

export default function AdminDashboardPage() {
  const { data: user } = useMe();
  const { data: tenantsData, isLoading, refetch, isFetching } = useAllTenants();
  const suspendTenant = useSuspendTenant();
  const activateTenant = useActivateTenant();
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  if (isLoading) return <Spinner />;

  if (user && user.role !== 'platform_admin') {
    return (
      <div className="container py-8">
        <Alert variant="destructive">
          Access Denied. Only Platform Administrators can access the SaaS Owner portal.
        </Alert>
      </div>
    );
  }

  const tenants = tenantsData?.results ?? [];
  const activeCount = tenants.filter((t) => t.status === 'active').length;
  const suspendedCount = tenants.filter((t) => t.status === 'suspended').length;
  const totalHalls = tenants.reduce((acc, t) => acc + (t.hall_count || 0), 0);

  const handleToggleStatus = async (tenantId: string, currentStatus: string, tenantName: string) => {
    setActionSuccess(null);
    try {
      if (currentStatus === 'active') {
        const note = window.prompt(`Enter suspension reason for "${tenantName}":`, 'Compliance review pending');
        if (note !== null) {
          await suspendTenant.mutateAsync({ id: tenantId, note });
          setActionSuccess(`Tenant "${tenantName}" has been suspended successfully.`);
        }
      } else {
        await activateTenant.mutateAsync(tenantId);
        setActionSuccess(`Tenant "${tenantName}" has been reactivated to Active status.`);
      }
    } catch (err) {
      alert(`Operation failed: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-8 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Platform Admin Portal</h1>
          </div>
          <p className="text-muted-foreground">
            Multi-tenant SaaS operations, tenant lifecycle control, subscription tiers, and system analytics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button asChild size="sm">
            <a href="http://localhost:8000/admin/" target="_blank" rel="noreferrer">
              Django Admin <ExternalLink className="ml-1 h-3.5 w-3.5" />
            </a>
          </Button>
          <Button variant="secondary" asChild size="sm">
            <a href="http://localhost:8000/api/docs/" target="_blank" rel="noreferrer">
              API Docs <ExternalLink className="ml-1 h-3.5 w-3.5" />
            </a>
          </Button>
        </div>
      </div>

      {actionSuccess ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {actionSuccess}
        </Alert>
      ) : null}

      {/* KPI Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tenants</CardTitle>
            <Building2 className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCount}</div>
            <p className="text-xs text-muted-foreground">{tenants.length} total registered</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Suspended Accounts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{suspendedCount}</div>
            <p className="text-xs text-muted-foreground">Blocked from taking bookings</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Halls Live</CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalHalls}</div>
            <p className="text-xs text-muted-foreground">Across Indian metro locations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Recurring Rev</CardTitle>
            <TrendingUp className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{(activeCount * 12999).toLocaleString('en-IN')}</div>
            <p className="text-xs text-muted-foreground">+18% GST collected automatically</p>
          </CardContent>
        </Card>
      </div>

      {/* Tenants Management Table */}
      <Card>
        <CardHeader>
          <CardTitle>Tenant Organizations</CardTitle>
          <CardDescription>
            Independent businesses operating on the platform. Enforce data isolation and billing status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="p-3">Organization</th>
                  <th className="p-3">HQ / Location</th>
                  <th className="p-3">Halls</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Suspension Note</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-muted/50">
                    <td className="p-3 font-medium">
                      <div>{t.name}</div>
                      <div className="text-xs text-muted-foreground">subdomain: {t.subdomain || t.slug}</div>
                    </td>
                    <td className="p-3">
                      {t.city}, {t.state}
                    </td>
                    <td className="p-3 font-semibold">{t.hall_count} halls</td>
                    <td className="p-3">
                      <Badge variant={t.status === 'active' ? 'success' : 'destructive'} className="capitalize">
                        {t.status}
                      </Badge>
                    </td>
                    <td className="p-3 text-xs text-muted-foreground">
                      {t.suspension_note || '—'}
                    </td>
                    <td className="p-3 text-right">
                      {t.status === 'active' ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          disabled={suspendTenant.isPending}
                          onClick={() => handleToggleStatus(t.id, t.status, t.name)}
                        >
                          <Power className="mr-1 h-3.5 w-3.5" />
                          Suspend
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={activateTenant.isPending}
                          onClick={() => handleToggleStatus(t.id, t.status, t.name)}
                        >
                          <CheckCircle2 className="mr-1 h-3.5 w-3.5 text-success" />
                          Reactivate
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Plans Configuration */}
      <Card id="plans">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-primary" />
            <CardTitle>SaaS Subscription Plans</CardTitle>
          </div>
          <CardDescription>
            Multi-tenant tier limits, Razorpay gateway integration, and auto-suspension thresholds.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card className="border">
              <CardHeader>
                <Badge variant="outline" className="w-fit">Starter</Badge>
                <div className="pt-2 text-2xl font-bold">₹4,999 <span className="text-xs font-normal text-muted-foreground">/ month</span></div>
                <CardDescription>Ideal for single-location hall owners.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>✓ Up to 2 halls</p>
                <p>✓ 2 manager accounts</p>
                <p>✓ Basic booking calendar</p>
                <p>✓ 7 days payment grace period</p>
              </CardContent>
            </Card>

            <Card className="border-primary bg-primary/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="default">Professional (Most Popular)</Badge>
                </div>
                <div className="pt-2 text-2xl font-bold">₹12,999 <span className="text-xs font-normal text-muted-foreground">/ month</span></div>
                <CardDescription>For growing banquet chains and convention centers.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>✓ Up to 10 halls</p>
                <p>✓ 10 manager accounts</p>
                <p>✓ Recommendation engine ranking boost</p>
                <p>✓ Automated customer SMS/Email alerts</p>
                <p>✓ Full booking & revenue reports</p>
              </CardContent>
            </Card>

            <Card className="border">
              <CardHeader>
                <Badge variant="outline" className="w-fit">Enterprise</Badge>
                <div className="pt-2 text-2xl font-bold">₹29,999 <span className="text-xs font-normal text-muted-foreground">/ month</span></div>
                <CardDescription>Pan-India luxury resort & convention chains.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>✓ Unlimited halls & locations</p>
                <p>✓ Unlimited team managers</p>
                <p>✓ Dedicated Account Manager</p>
                <p>✓ Custom Subdomain & Branding</p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
