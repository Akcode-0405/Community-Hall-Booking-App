'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, MapPin, Phone, ShieldCheck, Star, Store } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { FormField } from '@/components/form-field';
import { Spinner } from '@/components/states';
import { useUpdateVendorProfile, useVendorProfile } from '@/hooks/use-vendor';
import { errorMessage } from '@/lib/api';

export default function VendorProfilePage() {
  const { data: profile, isLoading, refetch } = useVendorProfile();
  const updateProfile = useUpdateVendorProfile();
  const [success, setSuccess] = useState<string | null>(null);

  const [form, setForm] = useState({
    business_name: '',
    description: '',
    city: '',
    state: '',
    contact_email: '',
    contact_phone: '',
    years_of_experience: 5,
  });

  useEffect(() => {
    if (profile) {
      setForm({
        business_name: profile.business_name || '',
        description: profile.description || '',
        city: profile.city || '',
        state: profile.state || '',
        contact_email: profile.contact_email || '',
        contact_phone: profile.contact_phone || '',
        years_of_experience: profile.years_of_experience || 5,
      });
    }
  }, [profile]);

  if (isLoading) return <Spinner />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(null);
    try {
      await updateProfile.mutateAsync(form);
      setSuccess('Vendor business profile updated successfully.');
      refetch();
    } catch (err) {
      alert(`Update failed: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Store className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Vendor Business Profile</h1>
          </div>
          <p className="text-muted-foreground">
            Manage your public business listing seen by hall owners and event planners across India.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild size="sm">
            <Link href="/vendor/services">My Services</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/vendor/bookings">View Enquiries</Link>
          </Button>
        </div>
      </div>

      {success ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {success}
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Profile Card */}
        <Card className="border lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="success">Verified Vendor</Badge>
              <span className="flex items-center gap-1 text-sm font-semibold">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {profile?.avg_rating || '5.0'}
              </span>
            </div>
            <CardTitle className="pt-2 text-xl">{profile?.business_name}</CardTitle>
            <CardDescription className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {profile?.city}, {profile?.state}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>{profile?.description || 'Experienced event service partner serving premium weddings and banquet functions.'}</p>
            <div className="border-t pt-3 space-y-1">
              <p>Experience: <strong>{profile?.years_of_experience} years</strong></p>
              <p>Email: <strong>{profile?.contact_email}</strong></p>
              <p>Phone: <strong>{profile?.contact_phone || 'Available upon inquiry'}</strong></p>
            </div>
          </CardContent>
        </Card>

        {/* Edit Form */}
        <Card className="border lg:col-span-2">
          <CardHeader>
            <CardTitle>Edit Business Details</CardTitle>
            <CardDescription>
              Keep your contact information and operating territory up to date.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <FormField id="bname" label="Business Name">
                <Input
                  required
                  value={form.business_name}
                  onChange={(e) => setForm({ ...form, business_name: e.target.value })}
                />
              </FormField>

              <FormField id="bdesc" label="Business Overview / Bio">
                <Textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </FormField>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="city" label="City">
                  <Input
                    required
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                  />
                </FormField>
                <FormField id="state" label="State">
                  <Input
                    required
                    value={form.state}
                    onChange={(e) => setForm({ ...form, state: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="email" label="Contact Email">
                  <Input
                    type="email"
                    required
                    value={form.contact_email}
                    onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                  />
                </FormField>
                <FormField id="phone" label="Contact Phone">
                  <Input
                    value={form.contact_phone}
                    onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" disabled={updateProfile.isPending}>
                  {updateProfile.isPending ? 'Saving Changes...' : 'Save Profile'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
