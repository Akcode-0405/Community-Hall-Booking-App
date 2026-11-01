import { Loader2, Construction, AlertTriangle } from 'lucide-react';
import { ApiError, errorMessage } from '@/lib/api';

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground" role="status">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed p-10 text-center">
      <p className="font-medium">{title}</p>
      {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

/** Error display that distinguishes "feature not built yet" from real failures. */
export function QueryError({ error }: { error: unknown }) {
  if (error instanceof ApiError && error.isNotImplemented) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center">
        <Construction className="mx-auto h-8 w-8 text-muted-foreground" aria-hidden />
        <p className="mt-3 font-medium">Coming soon</p>
        <p className="mt-1 text-sm text-muted-foreground">
          This part of the platform is still being built. Check back shortly.
        </p>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3 rounded-lg border border-destructive/50 p-4 text-sm text-destructive" role="alert">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span>{errorMessage(error)}</span>
    </div>
  );
}
