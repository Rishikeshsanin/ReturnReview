import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "ReturnReview | Faculty Presentation",
  description: "Evidence-first inspection with human review",
};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body><main className="shell">
    <header className="topbar">
      <div>
        <Link className="brand" href="/" aria-label="ReturnReview dashboard">Return<span>Review</span></Link>
        <span className="brand-caption">Faculty presentation edition</span>
      </div>
      <nav className="nav" aria-label="Main navigation">
        <Link className="btn" href="/">Dashboard</Link>
        <Link className="btn" href="/policies">Policies</Link>
        <Link className="btn" href="/evaluation">Evaluation</Link>
        <Link className="btn primary" href="/cases/new">+ New inspection</Link>
      </nav>
    </header>
    {children}
  </main></body></html>;
}
