import { api } from "@/lib/api";

export default async function PoliciesPage(){
  let rows:any[]=[];
  try{rows=await api<any[]>("/api/policies")}catch{}
  return <>
    <div className="eyebrow">Evidence source • Controlled retrieval</div>
    <h1>Return policies</h1>
    <p className="muted">Gemini retrieves an exact matching policy through the read-only get_return_policy() tool. This small structured policy set does not require a vector database.</p>
    <div className="list">{rows.length?rows.map(p=><div className="card" key={p.policy_id}>
      <div className="section-row"><div><div className="eyebrow">{p.policy_id}</div><h2>{p.name}</h2></div><span className="pill blue">Version {p.version}</span></div>
      <div className="helper-box" style={{marginTop:18}}><strong>{p.section}</strong><p style={{marginBottom:0}}>{p.text}</p></div>
      <p className="section-subtitle">The AI may summarize evidence, but only the human reviewer can make the final return decision.</p>
    </div>):<div className="card"><h2>Policies unavailable</h2><p className="muted">Check the FastAPI connection and try again.</p></div>}</div>
  </>;
}
