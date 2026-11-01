'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { Check, Minus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState, QueryError, Spinner } from '@/components/states';
import { useHall } from '@/hooks/use-halls';
import type { HallDetail } from '@/lib/types';
import { cn, formatINR } from '@/lib/utils';

type Better = 'a' | 'b' | null;

function compareNum(a: number | null, b: number | null, higherIsBetter: boolean): Better {
  if (a === null || b === null || a === b) return null;
  return (a > b) === higherIsBetter ? 'a' : 'b';
}

const num = (v: string | null | undefined) => (v === null || v === undefined || v === '' ? null : Number(v));

interface Row {
  label: string;
  a: React.ReactNode;
  b: React.ReactNode;
  better?: Better;
}

function buildRows(a: HallDetail, b: HallDetail): Row[] {
  const amenities = Array.from(new Set([...a.amenities, ...b.amenities])).sort();
  const mandatory = (h: HallDetail) => h.additional_charges.filter((c) => c.is_mandatory);

  const rows: Row[] = [
    { label: 'Starting price', a: formatINR(a.starting_price), b: formatINR(b.starting_price), better: compareNum(num(a.starting_price), num(b.starting_price), false) },
    {
      label: 'Mandatory extra charges',
      a: mandatory(a).length ? mandatory(a).map((c) => c.name).join(', ') : 'None',
      b: mandatory(b).length ? mandatory(b).map((c) => c.name).join(', ') : 'None',
      better: compareNum(mandatory(a).length, mandatory(b).length, false),
    },
    { label: 'Location', a: [a.locality, a.city].filter(Boolean).join(', '), b: [b.locality, b.city].filter(Boolean).join(', ') },
    {
      label: 'Distance',
      a: a.distance_km != null ? `${a.distance_km.toFixed(1)} km` : '—',
      b: b.distance_km != null ? `${b.distance_km.toFixed(1)} km` : '—',
      better: compareNum(a.distance_km ?? null, b.distance_km ?? null, false),
    },
    { label: 'Max guests', a: a.capacity_max, b: b.capacity_max, better: compareNum(a.capacity_max, b.capacity_max, true) },
    { label: 'Indoor / outdoor', a: <span className="capitalize">{a.hall_type}</span>, b: <span className="capitalize">{b.hall_type}</span> },
    {
      label: 'Rating',
      a: a.avg_rating ? `${Number(a.avg_rating).toFixed(1)} ★ (${a.review_count})` : 'No reviews',
      b: b.avg_rating ? `${Number(b.avg_rating).toFixed(1)} ★ (${b.review_count})` : 'No reviews',
      better: compareNum(num(a.avg_rating), num(b.avg_rating), true),
    },
    { label: 'Amenities', a: `${a.amenities.length} listed`, b: `${b.amenities.length} listed`, better: compareNum(a.amenities.length, b.amenities.length, true) },
    ...amenities.map<Row>((name) => {
      const hasA = a.amenities.includes(name);
      const hasB = b.amenities.includes(name);
      const icon = (has: boolean) =>
        has ? <Check className="h-4 w-4 text-success" aria-label="Yes" /> : <Minus className="h-4 w-4 text-muted-foreground" aria-label="No" />;
      return { label: `· ${name}`, a: icon(hasA), b: icon(hasB), better: hasA === hasB ? null : hasA ? 'a' : 'b' };
    }),
    { label: 'Cancellation policy', a: a.cancellation_policy || '—', b: b.cancellation_policy || '—' },
  ];
  return rows;
}

function Comparison() {
  const params = useSearchParams();
  const idA = params.get('a') ?? undefined;
  const idB = params.get('b') ?? undefined;
  const hallA = useHall(idA);
  const hallB = useHall(idB);

  if (!idA || !idB) {
    return (
      <EmptyState
        title="Pick two halls to compare"
        description="Tick “Compare” on two halls in the search results."
        action={
          <Button asChild>
            <Link href="/halls">Browse halls</Link>
          </Button>
        }
      />
    );
  }
  if (hallA.isLoading || hallB.isLoading) return <Spinner />;
  if (hallA.error || hallB.error) return <QueryError error={hallA.error ?? hallB.error} />;
  if (!hallA.data || !hallB.data) return null;

  const a = hallA.data;
  const b = hallB.data;
  const rows = buildRows(a, b);
  const wins = { a: rows.filter((r) => r.better === 'a').length, b: rows.filter((r) => r.better === 'b').length };

  const header = (h: HallDetail, side: 'a' | 'b') => (
    <th scope="col" className="w-[38%] p-4 text-left align-top">
      {h.primary_photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={h.primary_photo_url} alt="" className="mb-3 aspect-[16/10] w-full rounded-md object-cover" />
      ) : null}
      <Link href={`/halls/${h.id}`} className="font-semibold hover:underline">
        {h.name}
      </Link>
      <p className="mt-1 text-xs font-normal text-muted-foreground">Better on {wins[side]} criteria</p>
    </th>
  );

  return (
    <Card className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-sm">
        <thead className="border-b">
          <tr>
            <th scope="col" className="w-[24%] p-4 text-left text-muted-foreground">
              <span className="sr-only">Criterion</span>
            </th>
            {header(a, 'a')}
            {header(b, 'b')}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-b last:border-0">
              <th scope="row" className="p-4 text-left font-medium text-muted-foreground">
                {row.label}
              </th>
              {(['a', 'b'] as const).map((side) => (
                <td key={side} className={cn('p-4 align-top', row.better === side && 'bg-success/10 font-medium text-success')}>
                  {row[side]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export default function ComparePage() {
  return (
    <div className="container space-y-6 py-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compare halls</h1>
        <p className="text-muted-foreground">Highlighted cells show which hall does better on each point.</p>
      </div>
      <Suspense fallback={<Spinner />}>
        <Comparison />
      </Suspense>
    </div>
  );
}
