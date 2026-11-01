'use client';

import { useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, DollarSign, Package, Plus, Settings2, Sparkles, Tag } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { FormField } from '@/components/form-field';
import { Spinner } from '@/components/states';
import { useCreateVendorService, useVendorCategories, useVendorServices } from '@/hooks/use-vendor';
import { errorMessage } from '@/lib/api';
import { formatINR } from '@/lib/utils';

export default function VendorServicesPage() {
  const { data: servicesData, isLoading, refetch } = useVendorServices();
  const { data: categories } = useVendorCategories();
  const createService = useCreateVendorService();

  const [showAdd, setShowAdd] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: '',
    category_id: '',
    description: '',
    base_price: '45000',
    pricing_unit: 'per event',
  });

  if (isLoading) return <Spinner />;

  const services = servicesData?.results ?? [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    try {
      const selectedCategory = form.category_id || (categories && categories[0]?.id ? categories[0].id : undefined);
      await createService.mutateAsync({
        title: form.title,
        description: form.description,
        base_price: form.base_price,
        pricing_unit: form.pricing_unit,
        category: selectedCategory,
        is_active: true,
      });
      setSuccessMsg(`Service package "${form.title}" added to your catalogue!`);
      setShowAdd(false);
      setForm({ ...form, title: '', description: '' });
      refetch();
    } catch (err) {
      alert(`Failed to add service: ${errorMessage(err)}`);
    }
  };

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-7 w-7 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Vendor Service Packages</h1>
          </div>
          <p className="text-muted-foreground">
            List your event services such as catering, floral decoration, photography, and live music.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShowAdd(!showAdd)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Service Package
          </Button>
          <Button variant="outline" asChild>
            <Link href="/vendor/bookings">View Enquiries</Link>
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
            <CardTitle>Create New Service Package</CardTitle>
            <CardDescription>
              Offer your specialized event services to customers booking halls.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="title" label="Service Title">
                  <Input
                    required
                    placeholder="e.g. Royal Traditional Mandap & Floral Decor"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                  />
                </FormField>

                <FormField id="category" label="Category">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    value={form.category_id}
                    onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                  >
                    {categories?.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>

              <FormField id="description" label="Service Description">
                <Textarea
                  placeholder="Detail what is included: setup time, equipment, staff, custom themes..."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </FormField>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField id="base_price" label="Base Price (₹)">
                  <Input
                    type="number"
                    required
                    value={form.base_price}
                    onChange={(e) => setForm({ ...form, base_price: e.target.value })}
                  />
                </FormField>

                <FormField id="pricing_unit" label="Pricing Unit">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    value={form.pricing_unit}
                    onChange={(e) => setForm({ ...form, pricing_unit: e.target.value })}
                  >
                    <option value="per event">Per Event</option>
                    <option value="per plate">Per Plate</option>
                    <option value="per day">Per Day</option>
                    <option value="per hour">Per Hour</option>
                  </select>
                </FormField>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAdd(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createService.isPending}>
                  {createService.isPending ? 'Publishing...' : 'Publish Service'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {services.map((s) => (
          <Card key={s.id} className="flex flex-col justify-between border">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base">{s.title}</CardTitle>
                <Badge variant="outline" className="capitalize">
                  {s.category_name || 'Event Service'}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2 text-xs">
                {s.description || 'Comprehensive service package provided for weddings and celebratory events.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="border-t pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-muted-foreground">Starting from:</span>
                  <div className="text-lg font-bold">
                    {formatINR(s.base_price)} <span className="text-xs font-normal text-muted-foreground">/ {s.pricing_unit}</span>
                  </div>
                </div>
                <Badge variant="success">Active</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
