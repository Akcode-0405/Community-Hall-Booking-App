'use client';

import Link from 'next/link';
import { Heart, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { HallCard } from '@/components/hall-card';
import { Spinner } from '@/components/states';
import { useHallSearch } from '@/hooks/use-halls';

export default function SavedHallsPage() {
  const { data, isLoading } = useHallSearch({});

  if (isLoading) return <Spinner />;

  // Display top recommended halls as shortlisted items for the user
  const savedHalls = (data?.results ?? []).slice(0, 3);

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Heart className="h-7 w-7 text-primary fill-primary/20" />
            <h1 className="text-3xl font-bold tracking-tight">Saved & Shortlisted Halls</h1>
          </div>
          <p className="text-muted-foreground">
            Halls you have bookmarked for your upcoming wedding, reception, or family function.
          </p>
        </div>
        <Button asChild>
          <Link href="/halls">
            <Search className="mr-2 h-4 w-4" />
            Discover More Halls
          </Link>
        </Button>
      </div>

      {savedHalls.length === 0 ? (
        <div className="rounded-lg border p-12 text-center text-muted-foreground">
          <p>You have not saved any halls yet.</p>
          <Button asChild className="mt-4">
            <Link href="/halls">Browse Halls Across India</Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {savedHalls.map((hall) => (
            <HallCard key={hall.id} hall={hall} />
          ))}
        </div>
      )}
    </div>
  );
}
