export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <div className="container flex justify-center py-12 md:py-20">{children}</div>;
}
