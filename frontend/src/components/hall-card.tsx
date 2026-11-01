import Link from 'next/link';
import { MapPin, Star, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import type { HallSummary } from '@/lib/types';
import { formatINR } from '@/lib/utils';

interface HallCardProps {
  hall: HallSummary;
  selected?: boolean;
  onToggleCompare?: (hall: HallSummary) => void;
}

export function HallCard({ hall, selected, onToggleCompare }: HallCardProps) {
  return (
    <Card className="flex flex-col overflow-hidden">
      <Link href={`/halls/${hall.id}`} className="block aspect-[16/10] bg-muted">
        {hall.primary_photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={hall.primary_photo_url} alt={hall.name} className="h-full w-full object-cover" loading="lazy" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">No photo</div>
        )}
      </Link>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <Link href={`/halls/${hall.id}`} className="font-semibold leading-snug hover:underline">
            {hall.name}
          </Link>
          {typeof hall.match_score === 'number' ? <Badge variant="success">{Math.round(hall.match_score)}% match</Badge> : null}
        </div>
        <div className="space-y-1 text-sm text-muted-foreground">
          <p className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4" aria-hidden />
            {[hall.locality, hall.city].filter(Boolean).join(', ')}
            {hall.distance_km != null ? ` · ${hall.distance_km.toFixed(1)} km` : ''}
          </p>
          <p className="flex items-center gap-1.5">
            <Users className="h-4 w-4" aria-hidden />
            {hall.capacity_min}–{hall.capacity_max} guests · <span className="capitalize">{hall.hall_type}</span>
          </p>
          <p className="flex items-center gap-1.5">
            <Star className="h-4 w-4" aria-hidden />
            {hall.avg_rating ? `${Number(hall.avg_rating).toFixed(1)} (${hall.review_count})` : 'No reviews yet'}
          </p>
        </div>
        <div className="mt-auto flex items-center justify-between pt-2">
          <p>
            <span className="text-xs text-muted-foreground">From </span>
            <span className="font-semibold">{formatINR(hall.starting_price)}</span>
          </p>
          {onToggleCompare ? (
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input type="checkbox" checked={Boolean(selected)} onChange={() => onToggleCompare(hall)} className="h-4 w-4 accent-[hsl(var(--primary))]" />
              Compare
            </label>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
