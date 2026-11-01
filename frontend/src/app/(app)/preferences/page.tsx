'use client';

import { useEffect, useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/form-field';
import { EmptyState, QueryError, Spinner } from '@/components/states';
import { useMe, usePreferences, useUpdatePreferences } from '@/hooks/use-auth';
import { ApiError, errorMessage } from '@/lib/api';
import type { CustomerPreference } from '@/lib/types';

type WeightKey = 'weight_budget' | 'weight_capacity' | 'weight_proximity' | 'weight_amenities' | 'weight_rating';

const WEIGHTS: { key: WeightKey; label: string; help: string }[] = [
  { key: 'weight_budget', label: 'Budget fit', help: 'How closely the price matches your budget' },
  { key: 'weight_capacity', label: 'Capacity fit', help: 'How well the hall size suits your guest count' },
  { key: 'weight_proximity', label: 'Distance', help: 'How close the hall is to you' },
  { key: 'weight_amenities', label: 'Amenities', help: 'How many of your must-have amenities it has' },
  { key: 'weight_rating', label: 'Ratings', help: 'Review score (adjusted so few-review halls are not over-ranked)' },
];

type Form = Pick<
  CustomerPreference,
  'preferred_city' | 'preferred_state' | 'preferred_hall_type' | WeightKey
> & { budget_min: string; budget_max: string; preferred_capacity: string };

function toForm(p: CustomerPreference): Form {
  return {
    preferred_city: p.preferred_city,
    preferred_state: p.preferred_state,
    preferred_hall_type: p.preferred_hall_type,
    budget_min: p.budget_min ?? '',
    budget_max: p.budget_max ?? '',
    preferred_capacity: p.preferred_capacity?.toString() ?? '',
    weight_budget: p.weight_budget,
    weight_capacity: p.weight_capacity,
    weight_proximity: p.weight_proximity,
    weight_amenities: p.weight_amenities,
    weight_rating: p.weight_rating,
  };
}

export default function PreferencesPage() {
  const { data: user } = useMe();
  const isCustomer = user?.role === 'customer';
  const prefs = usePreferences(isCustomer);
  const update = useUpdatePreferences();
  const [form, setForm] = useState<Form | null>(null);
  const fieldErrors = update.error instanceof ApiError ? update.error.fieldErrors : {};

  useEffect(() => {
    if (prefs.data) setForm(toForm(prefs.data));
  }, [prefs.data]);

  if (user && !isCustomer) {
    return <EmptyState title="Preferences are for customers" description="Hall recommendations are personalised for customer accounts." />;
  }
  if (prefs.isError) return <QueryError error={prefs.error} />;
  if (!form) return <Spinner />;

  const total = WEIGHTS.reduce((sum, w) => sum + form[w.key], 0);
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm((f) => (f ? { ...f, [k]: v } : f));

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    update.mutate({
      ...form,
      budget_min: form.budget_min || null,
      budget_max: form.budget_max || null,
      preferred_capacity: form.preferred_capacity ? Number(form.preferred_capacity) : null,
    });
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto grid max-w-3xl gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Match preferences</h1>
        <p className="text-muted-foreground">These settings decide how halls are ranked in your recommendations.</p>
      </div>

      {update.isSuccess ? <Alert variant="success">Preferences saved.</Alert> : null}
      {update.isError ? <Alert variant="destructive">{errorMessage(update.error)}</Alert> : null}

      <Card>
        <CardHeader>
          <CardTitle>What you&apos;re looking for</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <FormField id="preferred_city" label="Preferred city">
            <Input value={form.preferred_city} onChange={(e) => set('preferred_city', e.target.value)} />
          </FormField>
          <FormField id="preferred_state" label="Preferred state">
            <Input value={form.preferred_state} onChange={(e) => set('preferred_state', e.target.value)} />
          </FormField>
          <FormField id="budget_min" label="Budget from (₹)" error={fieldErrors.budget_min}>
            <Input type="number" min={0} value={form.budget_min} onChange={(e) => set('budget_min', e.target.value)} />
          </FormField>
          <FormField id="budget_max" label="Budget up to (₹)" error={fieldErrors.budget_max}>
            <Input type="number" min={0} value={form.budget_max} onChange={(e) => set('budget_max', e.target.value)} />
          </FormField>
          <FormField id="preferred_capacity" label="Typical guest count">
            <Input type="number" min={1} value={form.preferred_capacity} onChange={(e) => set('preferred_capacity', e.target.value)} />
          </FormField>
          <FormField id="preferred_hall_type" label="Indoor / outdoor">
            <Select value={form.preferred_hall_type} onChange={(e) => set('preferred_hall_type', e.target.value as Form['preferred_hall_type'])}>
              <option value="">No preference</option>
              <option value="indoor">Indoor</option>
              <option value="outdoor">Outdoor</option>
              <option value="both">Indoor + outdoor</option>
            </Select>
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What matters most</CardTitle>
          <CardDescription>Weights are relative. They don&apos;t need to add up to 100; we normalise them.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {WEIGHTS.map(({ key, label, help }) => {
            const share = total ? Math.round((form[key] / total) * 100) : 0;
            return (
              <div key={key} className="space-y-1.5">
                <div className="flex items-baseline justify-between gap-4">
                  <label htmlFor={key} className="text-sm font-medium">
                    {label}
                  </label>
                  <span className="text-sm tabular-nums text-muted-foreground">{share}% of score</span>
                </div>
                <input
                  id={key}
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={form[key]}
                  onChange={(e) => set(key, Number(e.target.value))}
                  className="w-full accent-[hsl(var(--primary))]"
                  aria-describedby={`${key}-help`}
                />
                <p id={`${key}-help`} className="text-xs text-muted-foreground">
                  {help}
                </p>
              </div>
            );
          })}
          {total === 0 ? <Alert variant="destructive">Set at least one weight above zero.</Alert> : null}
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={update.isPending || total === 0}>
            {update.isPending ? 'Saving…' : 'Save preferences'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
