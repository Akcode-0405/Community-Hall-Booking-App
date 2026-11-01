'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Building2, CheckCircle2, MapPin, Plus, Star, Users } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { FormField } from '@/components/form-field';
import { Spinner } from '@/components/states';
import { useMe } from '@/hooks/use-auth';
import { useCreateTenantHall, useTenantHalls, useTenantLocations } from '@/hooks/use-tenant';
import { errorMessage } from '@/lib/api';
import { formatINR } from '@/lib/utils';

export default function TenantHallsPage() {
  const { data: user } = useMe();
  const { data: hallsData, isLoading, refetch } = useTenantHalls();
  const { data: locationsData } = useTenantLocations();
  const createHall = useCreateTenantHall();

  const [showAddModal, setShowAddModal] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: '',
    location_id: '',
    description: '',
    capacity_min: '100',
    capacity_max: '800',
    hall_type: 'indoor',
    base_price_per_day: '85000',
    base_price_per_hour: '8500',
    cleaning_fee: '4500',
    security_deposit: '15000',
    gst_percentage: '18.0',
    cancellation_policy: 'Full refund 7 days prior. 50% refund 48 hours prior.',
  });

  if (isLoading) return <Spinner />;

  if (user && !['tenant_owner', 'tenant_manager', 'platform_admin'].includes(user.role)) {
    return (
      <div className="container py-8">
        <Alert variant="destructive">
          Access Restricted: Only Tenant Owners and Hall Managers can access this portal.
        </Alert>
      </div>
    );
  }

  const halls = hallsData?.results ?? [];
  const locations = locationsData?.results ?? [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    try {
      const selectedLocation = form.location_id || (locations[0]?.id ?? '');
      if (!selectedLocation) {
        alert('Please create or select a location first.');
        return;
      }
      await createHall.mutateAsync({
        location: selectedLocation,
        name: form.name,
        description: form.description,
        capacity_min: Number(form.capacity_min),
        capacity_max: Number(form.capacity_max),
        hall_type: form.hall_type,
        base_price_per_day: form.base_price_per_day,
        base_price_per_hour: form.base_price_per_hour,
        cleaning_fee: form.cleaning_fee,
        security_deposit: form.security_deposit,
        gst_percentage: form.gst_percentage,
        cancellation_policy: form.cancellation_policy,
        is_active: true,
        is_published: true,
        photos: [
          'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1200&q=80',
        ],
      });
      setSuccessMsg(`Hall "${form.name}" has been created and published successfully.`);
      setShowAddModal(false);
      setForm({ ...form, name: '', description: '' });
      refetch();
    } catch (err) {
      alert(`Failed to add hall: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-8 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Halls & Venues</h1>
          </div>
          <p className="text-muted-foreground">
            Manage your banquet halls, convention centers, daily pricing, and capacity limits.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowAddModal(!showAddModal)}>
            <Plus className="mr-2 h-4 w-4" />
            Add New Hall
          </Button>
          <Button variant="outline" asChild>
            <Link href="/tenant/bookings">View Bookings Queue</Link>
          </Button>
        </div>
      </div>

      {successMsg ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {successMsg}
        </Alert>
      ) : null}

      {/* Add Hall Form Dialog */}
      {showAddModal ? (
        <Card className="border-primary bg-card shadow-lg">
          <CardHeader>
            <CardTitle>Add New Hall to Organisation</CardTitle>
            <CardDescription>
              Provide hall specifications, guest capacity, and pricing policies.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="name" label="Hall Name">
                  <Input
                    required
                    placeholder="e.g. Sapphire Grand Ballroom"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </FormField>

                <FormField id="location" label="Location">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    value={form.location_id}
                    onChange={(e) => setForm({ ...form, location_id: e.target.value })}
                  >
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.city}, {loc.state})
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>

              <FormField id="description" label="Description">
                <Textarea
                  placeholder="Describe your hall, air conditioning, stage, acoustics, and suitability for weddings or conferences..."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </FormField>

              <div className="grid gap-4 sm:grid-cols-3">
                <FormField id="hall_type" label="Venue Type">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    value={form.hall_type}
                    onChange={(e) => setForm({ ...form, hall_type: e.target.value })}
                  >
                    <option value="indoor">Indoor (AC Banquet)</option>
                    <option value="outdoor">Outdoor (Lawn / Open Air)</option>
                    <option value="both">Both (Indoor + Lawn)</option>
                  </select>
                </FormField>

                <FormField id="capacity_min" label="Min Guests">
                  <Input
                    type="number"
                    value={form.capacity_min}
                    onChange={(e) => setForm({ ...form, capacity_min: e.target.value })}
                  />
                </FormField>

                <FormField id="capacity_max" label="Max Capacity">
                  <Input
                    type="number"
                    value={form.capacity_max}
                    onChange={(e) => setForm({ ...form, capacity_max: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <FormField id="base_price_per_day" label="Full Day Price (₹)">
                  <Input
                    type="number"
                    required
                    value={form.base_price_per_day}
                    onChange={(e) => setForm({ ...form, base_price_per_day: e.target.value })}
                  />
                </FormField>

                <FormField id="base_price_per_hour" label="Hourly Rate (₹)">
                  <Input
                    type="number"
                    value={form.base_price_per_hour}
                    onChange={(e) => setForm({ ...form, base_price_per_hour: e.target.value })}
                  />
                </FormField>

                <FormField id="cleaning_fee" label="Cleaning Fee (₹)">
                  <Input
                    type="number"
                    value={form.cleaning_fee}
                    onChange={(e) => setForm({ ...form, cleaning_fee: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createHall.isPending}>
                  {createHall.isPending ? 'Saving...' : 'Create & Publish Hall'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {/* Halls Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {halls.map((h) => (
          <Card key={h.id} className="overflow-hidden">
            <div className="aspect-[16/10] bg-muted">
              {h.primary_photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={h.primary_photo_url}
                  alt={h.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  No image
                </div>
              )}
            </div>
            <CardHeader className="p-4 pb-2">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-lg">{h.name}</CardTitle>
                <Badge variant="outline" className="capitalize">
                  {h.hall_type}
                </Badge>
              </div>
              <CardDescription className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {h.locality}, {h.city}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-4 pt-0">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {h.capacity_min}–{h.capacity_max} guests
                </span>
                <span className="flex items-center gap-1">
                  <Star className="h-4 w-4 text-warning" />
                  {h.avg_rating || '5.0'} ({h.review_count} reviews)
                </span>
              </div>
              <div className="flex items-center justify-between border-t pt-2">
                <div>
                  <span className="text-xs text-muted-foreground">Full Day: </span>
                  <span className="font-semibold">{formatINR(h.starting_price)}</span>
                </div>
                <Button asChild size="sm" variant="outline">
                  <Link href={`/halls/${h.id}`}>Preview Page</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
