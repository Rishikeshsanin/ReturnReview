import Link from "next/link";
import { api } from "@/lib/api";

type CaseRow={id:string;external_case_id:string;product_name:string;status:string;created_at:string};
type Readiness={
  status:string;
  database?:{ok:boolean;backend:string;durable:boolean};
  cv_ready?:boolean;
  llm_ready?:boolean;
  blockers?:string[];
};

async function getCases():Promise<CaseRow[]>{
  try{return await api<CaseRow[]>("/api/cases")}catch{return []}
}

async function getReadiness():Promise<Readiness>{
  try{return await api<Readiness>("/readiness")}catch{return {status:"unavailable",blockers:["api_unavailable"]}}
}

export default async function Home(){
  const [cases,readiness]=await Promise.all([getCases(),getReadiness()]);
  const ready=cases.filter(c=>c.status==="READY_FOR_REVIEW").length;
  const closed=cases.filter(c=>["APPROVED","REJECTED"].includes(c.status)).length;
  const persistence=readiness.database?.durable===true;
  const cvReady=readiness.cv_ready===true;
  const llmReady=readiness.llm_ready===true;
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

    <section className="card" style={{marginBottom:16}}>
      <div className="section-row"><h2>System readiness</h2><span className="pill">{readiness.status}</span></div>
      <div className="stats">
        <div className="stat"><span className="muted">Persistent evidence</span><strong>{persistence?"Ready":"Setup"}</strong></div>
        <div className="stat"><span className="muted">Computer vision</span><strong>{cvReady?"Ready":"Awaiting data"}</strong></div>
        <div className="stat"><span className="muted">Gemini review</span><strong>{llmReady?"Ready":"Disabled"}</strong></div>
      </div>
      {(readiness.blockers?.length||0)>0&&<p className="muted">Open items: {readiness.blockers?.join(" · ").replaceAll("_"," ")}</p>}
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
