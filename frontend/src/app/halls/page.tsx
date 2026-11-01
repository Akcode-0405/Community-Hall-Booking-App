'use client';

import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { GitCompare, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { HallCard } from '@/components/hall-card';
import { EmptyState, QueryError, Spinner } from '@/components/states';
import { useHallSearch, type HallFilters } from '@/hooks/use-halls';
import type { HallSummary } from '@/lib/types';

const FILTER_KEYS = ['q', 'city', 'state', 'event_date', 'guests', 'budget_max', 'hall_type', 'min_rating', 'ordering', 'page'] as const;

function readFilters(params: URLSearchParams): HallFilters {
  const num = (k: string) => (params.get(k) ? Number(params.get(k)) : undefined);
  return {
    q: params.get('q') ?? undefined,
    city: params.get('city') ?? undefined,
    state: params.get('state') ?? undefined,
    event_date: params.get('event_date') ?? undefined,
    guests: num('guests'),
    budget_max: num('budget_max'),
    hall_type: params.get('hall_type') ?? undefined,
    min_rating: num('min_rating'),
    ordering: params.get('ordering') ?? undefined,
    page: num('page'),
  };
}

function SearchView() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const filters = readFilters(params);
  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) ?? ''])),
  );
  const [showFilters, setShowFilters] = useState(false);
  const [compare, setCompare] = useState<HallSummary[]>([]);
  const search = useHallSearch(filters);

  function apply(next: Record<string, string>) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(next)) if (v) qs.set(k, v);
    router.push(`${pathname}?${qs}`);
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    apply({ ...draft, page: '' });
    setShowFilters(false);
  }

  function toggleCompare(hall: HallSummary) {
    setCompare((list) =>
      list.some((h) => h.id === hall.id) ? list.filter((h) => h.id !== hall.id) : [...list, hall].slice(-2),
    );
  }

  const field = (key: string) => ({
    value: draft[key] ?? '',
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setDraft((d) => ({ ...d, [key]: e.target.value })),
  });

  const page = filters.page ?? 1;
  const data = search.data;

  return (
    <div className="container py-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight">Find a hall</h1>
        <Button variant="outline" className="lg:hidden" onClick={() => setShowFilters((s) => !s)} aria-expanded={showFilters}>
          <SlidersHorizontal className="h-4 w-4" aria-hidden /> Filters
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <form onSubmit={onSubmit} className={`${showFilters ? 'block' : 'hidden'} space-y-4 lg:block`} aria-label="Search filters">
          <Card className="space-y-4 p-4">
            <div className="space-y-2">
              <Label htmlFor="q">Keyword</Label>
              <Input id="q" placeholder="Hall name or locality" {...field('q')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input id="city" placeholder="e.g. Chennai" {...field('city')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event_date">Event date</Label>
              <Input id="event_date" type="date" {...field('event_date')} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="guests">Guests</Label>
                <Input id="guests" type="number" min={1} {...field('guests')} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="budget_max">Max budget ₹</Label>
                <Input id="budget_max" type="number" min={0} {...field('budget_max')} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="hall_type">Indoor / outdoor</Label>
              <Select id="hall_type" {...field('hall_type')}>
                <option value="">Any</option>
                <option value="indoor">Indoor</option>
                <option value="outdoor">Outdoor</option>
                <option value="both">Both</option>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="min_rating">Minimum rating</Label>
              <Select id="min_rating" {...field('min_rating')}>
                <option value="">Any</option>
                <option value="3">3+ ★</option>
                <option value="4">4+ ★</option>
                <option value="4.5">4.5+ ★</option>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="ordering">Sort by</Label>
              <Select id="ordering" {...field('ordering')}>
                <option value="">Best match</option>
                <option value="price">Price: low to high</option>
                <option value="-price">Price: high to low</option>
                <option value="-rating">Top rated</option>
                <option value="distance">Nearest</option>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button type="submit" className="flex-1">
                Apply
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  const empty = Object.fromEntries(FILTER_KEYS.map((k) => [k, '']));
                  setDraft(empty);
                  apply(empty);
                }}
              >
                Reset
              </Button>
            </div>
          </Card>
        </form>

        <section aria-live="polite">
          {search.isLoading ? (
            <Spinner label="Searching halls…" />
          ) : search.isError ? (
            <QueryError error={search.error} />
          ) : !data?.results.length ? (
            <EmptyState title="No halls match your filters" description="Try another city, date or a higher budget." />
          ) : (
            <>
              <p className="mb-4 text-sm text-muted-foreground">
                {data.count} hall{data.count === 1 ? '' : 's'} found
              </p>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {data.results.map((hall) => (
                  <HallCard key={hall.id} hall={hall} selected={compare.some((h) => h.id === hall.id)} onToggleCompare={toggleCompare} />
                ))}
              </div>
              {data.total_pages > 1 ? (
                <nav className="mt-6 flex items-center justify-center gap-3" aria-label="Pagination">
                  <Button variant="outline" disabled={!data.previous} onClick={() => apply({ ...draft, page: String(page - 1) })}>
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {data.total_pages}
                  </span>
                  <Button variant="outline" disabled={!data.next} onClick={() => apply({ ...draft, page: String(page + 1) })}>
                    Next
                  </Button>
                </nav>
              ) : null}
            </>
          )}
        </section>
      </div>

      {compare.length ? (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-background/95 backdrop-blur">
          <div className="container flex flex-wrap items-center justify-between gap-3 py-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <GitCompare className="h-4 w-4 text-primary" aria-hidden />
              {compare.map((h) => (
                <span key={h.id} className="flex items-center gap-1 rounded-full border px-3 py-1">
                  {h.name}
                  <button onClick={() => toggleCompare(h)} aria-label={`Remove ${h.name} from comparison`}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {compare.length < 2 ? <span className="text-muted-foreground">Select one more hall</span> : null}
            </div>
            <Button asChild disabled={compare.length < 2}>
              <Link
                href={compare.length === 2 ? `/compare?a=${compare[0].id}&b=${compare[1].id}${filters.event_date ? `&date=${filters.event_date}` : ''}` : '#'}
                aria-disabled={compare.length < 2}
              >
                Compare
              </Link>
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function HallsPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <SearchView />
    </Suspense>
  );
}
