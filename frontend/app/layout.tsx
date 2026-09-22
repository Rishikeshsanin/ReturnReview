import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "ReturnReview",
  description: "Evidence-first AI return inspection",
};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body><main className="shell">
    <header className="topbar">
      <Link className="brand" href="/">Return<span>Review</span></Link>
      <nav className="nav">
        <Link className="btn" href="/">Cases</Link>
        <Link className="btn" href="/policies">Policies</Link>
        <Link className="btn" href="/evaluation">Evaluation</Link>
        <Link className="btn primary" href="/cases/new">New inspection</Link>
      </nav>
    </header>
    {children}
  </main></body></html>;
}
