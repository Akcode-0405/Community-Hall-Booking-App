'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Building2, CheckCircle2, MapPin, Plus } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/form-field';
import { Spinner } from '@/components/states';
import { useCreateTenantLocation, useTenantLocations } from '@/hooks/use-tenant';
import { errorMessage } from '@/lib/api';

export default function TenantLocationsPage() {
  const { data: locationsData, isLoading, refetch } = useTenantLocations();
  const createLocation = useCreateTenantLocation();
  const [showAdd, setShowAdd] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: '',
    address_line_1: '',
    address_line_2: '',
    city: 'Bangalore',
    state: 'Karnataka',
    pin_code: '560034',
  });

  if (isLoading) return <Spinner />;

  const locations = locationsData?.results ?? [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    try {
      await createLocation.mutateAsync(form);
      setSuccessMsg(`Location "${form.name}" was added successfully.`);
      setShowAdd(false);
      setForm({
        name: '',
        address_line_1: '',
        address_line_2: '',
        city: 'Bangalore',
        state: 'Karnataka',
        pin_code: '560034',
      });
      refetch();
    } catch (err) {
      alert(`Failed to add location: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Business Locations</h1>
          </div>
          <p className="text-muted-foreground">
            Manage your branches across Indian cities where your halls and banquet spaces operate.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowAdd(!showAdd)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Location
          </Button>
          <Button variant="outline" asChild>
            <Link href="/tenant/halls">View Halls</Link>
          </Button>
        </div>
      </div>

      {successMsg ? (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          {successMsg}
        </Alert>
      ) : null}

      {showAdd ? (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Add New Business Location</CardTitle>
            <CardDescription>
              New branch address where you can associate multiple halls.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="loc_name" label="Branch / Complex Name">
                  <Input
                    required
                    placeholder="e.g. Koramangala Convention Hub"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </FormField>
                <FormField id="addr1" label="Address Line 1">
                  <Input
                    required
                    placeholder="e.g. 14, 80 Feet Road, 4th Block"
                    value={form.address_line_1}
                    onChange={(e) => setForm({ ...form, address_line_1: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
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
                <FormField id="pincode" label="PIN Code">
                  <Input
                    required
                    value={form.pin_code}
                    onChange={(e) => setForm({ ...form, pin_code: e.target.value })}
                  />
                </FormField>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAdd(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createLocation.isPending}>
                  {createLocation.isPending ? 'Saving...' : 'Save Location'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {locations.map((loc) => (
          <Card key={loc.id} className="border">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <CardTitle className="text-base">{loc.name}</CardTitle>
                <Badge variant="outline">{loc.hall_count} Halls</Badge>
              </div>
              <CardDescription className="text-xs">
                {loc.address_line_1}
                {loc.address_line_2 ? `, ${loc.address_line_2}` : ''}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>
                {loc.city}, {loc.state} – {loc.pin_code}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
