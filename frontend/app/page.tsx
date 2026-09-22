import Link from "next/link";
import { api } from "@/lib/api";

type CaseRow={id:string;external_case_id:string;product_name:string;status:string;created_at:string};

async function getCases():Promise<CaseRow[]>{
  try{return await api<CaseRow[]>("/api/cases")}catch{return []}
}

export default async function Home(){
  const cases=await getCases();
  const ready=cases.filter(c=>c.status==="READY_FOR_REVIEW").length;
  const closed=cases.filter(c=>["APPROVED","REJECTED"].includes(c.status)).length;
  return <>
    <section className="hero">
      <div className="card">
        <div className="eyebrow">Evidence-first return inspection</div>
        <h1>Inspect visible damage. Ground every claim.</h1>
        <p className="muted">Computer vision localizes damage; policy retrieval and an LLM prepare a review; a human makes the final decision.</p>
        <div className="actions"><Link className="btn primary" href="/cases/new">Start new inspection</Link><Link className="btn" href="/evaluation">View evaluation</Link></div>
      </div>
      <div className="card">
        <div className="eyebrow">MVP scope</div>
        <h2>Cardboard boxes</h2>
        <p className="muted">Visible external damage only. Binary segmentation + OpenCLIP few-shot recognition.</p>
        <div className="pill">Human-in-the-loop</div>
      </div>
    </section>
    <section className="stats">
      <div className="card stat"><span className="muted">Total cases</span><strong>{cases.length}</strong></div>
      <div className="card stat"><span className="muted">Ready for review</span><strong>{ready}</strong></div>
      <div className="card stat"><span className="muted">Human decisions</span><strong>{closed}</strong></div>
    </section>
    <div className="section-title"><h2>Recent cases</h2><Link className="btn" href="/cases/new">New case</Link></div>
    <div className="case-grid">{cases.length===0?<div className="card muted">No cases yet. Create the first return inspection.</div>:cases.slice(0,8).map(c=><Link className="card case-row" key={c.id} href={`/cases/${c.id}`}><strong>{c.external_case_id}</strong><span>{c.product_name}</span><span className="pill">{c.status}</span><span className="muted">{new Date(c.created_at).toLocaleDateString()}</span></Link>)}</div>
  </>;
}
