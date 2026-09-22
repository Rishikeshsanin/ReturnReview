import { api } from "@/lib/api";

export default async function PoliciesPage(){
  let rows:any[]=[];
  try{rows=await api<any[]>("/api/policies")}catch{}
  return <>
    <div className="eyebrow">Evidence source</div>
    <h1>Return policies</h1>
    <div className="list">{rows.map(p=><div className="card" key={p.policy_id}>
      <div className="section-row"><h2>{p.name}</h2><span className="pill">v{p.version}</span></div>
      <strong>{p.section}</strong><p className="muted">{p.text}</p>
    </div>)}</div>
  </>;
}
