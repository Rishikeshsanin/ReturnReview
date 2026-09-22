import { api } from "@/lib/api";

export default async function EvaluationPage(){
  let data:any={status:"unavailable"};
  try{data=await api<any>("/api/metrics")}catch{}
  return <>
    <div className="eyebrow">Academic evaluation</div>
    <h1>Evaluation dashboard</h1>
    <div className="card">
      {data.status!=="evaluated"?<>
        <h2>Metrics not generated yet</h2>
        <p className="muted">This page intentionally does not display invented numbers. Results appear after the held-out evaluation scripts produce the metrics artifact.</p>
      </>:<pre>{JSON.stringify(data,null,2)}</pre>}
    </div>
  </>;
}
