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

function humanStatus(status:string){return status.toLowerCase().replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}
function statusStyle(status:string){return ["APPROVED","READY_FOR_REVIEW"].includes(status)?"good":["CV_COMPLETE","GENERATING_REVIEW","READY_FOR_INSPECTION"].includes(status)?"blue":"warning"}

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
        <div className="eyebrow">ReturnReview • Interactive faculty demo</div>
        <h1>From box damage to a review you can trust.</h1>
        <p className="muted">Upload evidence, inspect visible damage, generate a grounded Gemini review, then make the human decision. Every step is traceable.</p>
        <div className="actions">
          <Link className="btn primary action" href="/cases/new">+ Start a return inspection</Link>
          <Link className="btn action" href="/evaluation">Explore verified results</Link>
        </div>
      </div>
      <div className="card">
        <div className="eyebrow">How it works</div>
        <h2>Four simple stages</h2>
        <div className="list">
          <div className="item"><strong>01 · Upload evidence</strong><div className="muted">Add 2–4 views of one cardboard box.</div></div>
          <div className="item"><strong>02 · Inspect damage</strong><div className="muted">MobileNetV3-Small + YOLO11n-seg.</div></div>
          <div className="item"><strong>03 · Generate review</strong><div className="muted">Gemini uses three read-only tools and policy.</div></div>
          <div className="item"><strong>04 · Human decides</strong><div className="muted">Approve, reject, or request more evidence.</div></div>
        </div>
      </div>
    </section>

    <section className="card" style={{marginBottom:20}}>
      <div className="section-row"><div><div className="eyebrow">Live system</div><h2>System readiness</h2></div><span className={`pill ${readiness.status==="ready"?"good":"warning"}`}>{readiness.status==="ready"?"Ready for inspection":humanStatus(readiness.status)}</span></div>
      <p className="muted">These indicators show configuration readiness; they do not guarantee Gemini provider availability.</p>
      <div className="stats">
        <div className="stat"><span className="muted">Evidence database</span><strong style={{color:persistence?"var(--good)":"var(--warn)"}}>{persistence?"Connected":"Check setup"}</strong><small className="muted">PostgreSQL persistence</small></div>
        <div className="stat"><span className="muted">Computer vision</span><strong style={{color:cvReady?"var(--good)":"var(--warn)"}}>{cvReady?"Ready":"Unavailable"}</strong><small className="muted">Model checkpoints loaded</small></div>
        <div className="stat"><span className="muted">Gemini review</span><strong style={{color:llmReady?"var(--good)":"var(--warn)"}}>{llmReady?"Configured":"Disabled"}</strong><small className="muted">Live provider calls may vary</small></div>
      </div>
      {(readiness.blockers?.length||0)>0&&<div className="notice error" style={{marginTop:18}} role="alert">Open items: {readiness.blockers?.join(" · ").replaceAll("_"," ")}</div>}
    </section>

    <section className="stats" aria-label="Case statistics">
      <div className="card stat"><span className="muted">Total return cases</span><strong>{cases.length}</strong></div>
      <div className="card stat"><span className="muted">Awaiting human review</span><strong>{ready}</strong></div>
      <div className="card stat"><span className="muted">Human decisions recorded</span><strong>{closed}</strong></div>
    </section>
    <div className="section-title"><div><div className="eyebrow">Your workspace</div><h2>Recent inspections</h2></div><Link className="btn primary" href="/cases/new">+ Create a case</Link></div>
    <div className="case-grid">{cases.length===0?
      <div className="card empty-state"><h3>No cases yet</h3><p className="muted" style={{margin:"0 auto 18px"}}>Start by creating a return case and uploading two photos of a cardboard box.</p><Link href="/cases/new" className="btn primary action">Create your first case</Link></div>
      :cases.slice(0,10).map(c=><Link className="card case-row" key={c.id} href={`/cases/${c.id}`}>
        <strong>{c.external_case_id}</strong><span>{c.product_name}</span><span className={`pill ${statusStyle(c.status)}`}>{humanStatus(c.status)}</span><span className="muted">{new Date(c.created_at).toLocaleDateString("en-IN")}</span>
      </Link>)}</div>
  </>;
}
