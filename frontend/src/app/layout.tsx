import type { Metadata, Viewport } from 'next';
import './globals.css';
import { Providers } from './providers';
import { SiteHeader } from '@/components/site-header';

export const metadata: Metadata = {
  title: { default: 'HallBooking — Find & book event halls across India', template: '%s · HallBooking' },
  description: 'Discover, compare and book community and event halls across India.',
};

export const viewport: Viewport = { width: 'device-width', initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-IN">
      <body className="font-sans antialiased">
        <Providers>
          <SiteHeader />
          <main className="min-h-[calc(100vh-4rem)]">{children}</main>
          <footer className="border-t py-6 text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} HallBooking. Made for events across India.
          </footer>
        </Providers>
      </body>
    </html>
  );
}
