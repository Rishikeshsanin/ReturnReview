import { api } from "@/lib/api";

export default async function EvaluationPage(){
  let data:any={status:"unavailable"};
  let readiness:any={status:"unavailable",blockers:["api_unavailable"]};
  try{[data,readiness]=await Promise.all([api<any>("/api/metrics"),api<any>("/readiness")])}catch{}
  return <>
    <div className="eyebrow">Academic evaluation</div>
    <h1>Evaluation dashboard</h1>

    <div className="card" style={{marginBottom:16}}>
      <div className="section-row"><h2>Readiness</h2><span className="pill">{readiness.status}</span></div>
      <p className="muted">This section reports configuration state only. It never substitutes readiness flags for held-out model metrics.</p>
      <div className="list">
        <div className="item"><strong>Persistent evidence</strong><div className="muted">{readiness.database?.durable?"configured":"not enabled in this deployment"}</div></div>
        <div className="item"><strong>Computer vision</strong><div className="muted">{readiness.cv_ready?"validated artifacts configured":"real trained checkpoint/prototypes still required"}</div></div>
        <div className="item"><strong>Gemini review</strong><div className="muted">{readiness.llm_ready?"enabled":"API key + production enablement still required"}</div></div>
      </div>
    </div>

    <div className="card">
      {data.status!=="evaluated"?<>
        <h2>Metrics not generated yet</h2>
        <p className="muted">This page intentionally does not display invented numbers. Results appear after the held-out evaluation scripts produce the metrics artifact.</p>
      </>:<pre>{JSON.stringify(data,null,2)}</pre>}
    </div>
  </>;
}
