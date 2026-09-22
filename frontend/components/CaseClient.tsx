"use client";
import { FormEvent, useState } from "react";
import { API, api } from "@/lib/api";

type CaseData = any;

export default function CaseClient({caseId,initial}:{caseId:string;initial:CaseData}){
  const [data,setData]=useState(initial);
  const [busy,setBusy]=useState("");
  const [error,setError]=useState("");

  async function refresh(){setData(await api(`/api/cases/${caseId}`))}
  async function upload(e:FormEvent<HTMLFormElement>){
    e.preventDefault();
    setBusy("upload");
    setError("");
    const form=new FormData(e.currentTarget);
    try{
      await api(`/api/cases/${caseId}/images`,{method:"POST",body:form});
      await refresh();
      e.currentTarget.reset();
    }catch(e){setError(e instanceof Error?e.message:"Upload failed")}
    finally{setBusy("")}
  }

  async function run(path:string,key:string){
    setBusy(key);setError("");
    try{await api(path,{method:"POST"});await refresh()}
    catch(e){setError(e instanceof Error?e.message:"Operation failed")}
    finally{setBusy("")}
  }

  async function decide(action:string){
    setBusy(action);setError("");
    try{
      await api(`/api/cases/${caseId}/decision`,{method:"POST",body:JSON.stringify({action})});
      await refresh();
    }catch(e){setError(e instanceof Error?e.message:"Decision failed")}
    finally{setBusy("")}
  }

  const review=data.ai_review;
  const findings=data.evidence?.findings || [];

  return <>
    {error&&<div className="notice error" style={{marginBottom:16}}>{error}</div>}
    <div className="section-title">
      <div>
        <div className="eyebrow">Case {data.case.external_case_id}</div>
        <h1>{data.case.product_name}</h1>
        <p className="muted">{data.case.customer_reason}</p>
      </div>
      <span className="pill">{data.case.status}</span>
    </div>

    <div className="result-grid">
      <section className="card">
        <div className="section-row"><h2>Visual evidence</h2><span className="pill">{data.images.length} views</span></div>
        {data.images.length===0
          ? <div className="evidence">Upload 2–4 views of the returned box.</div>
          : <div className="image-grid">{data.images.map((i:any)=><figure className="image-card" key={i.id}>
              <img src={`${API}${i.image_url}`} alt={`${i.view_label} view`} />
              <figcaption><strong>{i.view_label}</strong><span>Quality {i.quality_score?Math.round(i.quality_score*100)+"%":"n/a"}</span></figcaption>
              {i.quality_warning&&<small className="warn">{i.quality_warning}</small>}
            </figure>)}</div>}

        {findings.length>0&&<>
          <div className="section-row" style={{marginTop:22}}><h3>Detected regions</h3><span className="pill">{findings.length} findings</span></div>
          <div className="image-grid">{findings.map((f:any)=><figure className="image-card" key={f.finding_id}>
            {f.mask_path?<img src={`${API}/media/${f.mask_path}`} alt={`AI overlay ${f.defect_type}`} />:<div className="evidence small">Overlay unavailable</div>}
            <figcaption><strong>{f.defect_type}</strong><span>{Math.round((f.confidence||0)*100)}%</span></figcaption>
            <small className="muted">Affected visible area: {f.affected_area_percent?.toFixed?.(2) ?? "n/a"}%</small>
          </figure>)}</div>
        </>}

        <form className="form" onSubmit={upload} style={{marginTop:18}}>
          <div className="two">
            <input className="input" type="file" name="image" accept="image/jpeg,image/png,image/webp" required/>
            <select className="select" name="view_label" defaultValue="front">
              <option>front</option><option>back</option><option>left</option><option>right</option><option>top</option>
            </select>
          </div>
          <button className="btn" disabled={busy==="upload"}>{busy==="upload"?"Uploading...":"Add image"}</button>
        </form>
      </section>

      <aside className="card">
        <h2>Inspection workflow</h2>
        <div className="list">
          <div className="item">
            <span className="step">01</span><strong>Computer vision</strong>
            <p className="muted">OpenCLIP verification → YOLO damage mask → few-shot defect prototype.</p>
            <button className="btn primary" disabled={!!busy||!data.images.length} onClick={()=>run(`/api/cases/${caseId}/inspect`,"inspect")}>{busy==="inspect"?"Inspecting...":"Run inspection"}</button>
          </div>
          <div className="item">
            <span className="step">02</span><strong>Evidence-grounded review</strong>
            <p className="muted">Gemini may read case evidence and policy tools; it cannot make the final return decision.</p>
            <button className="btn" disabled={!!busy} onClick={()=>run(`/api/cases/${caseId}/ai-review`,"review")}>{busy==="review"?"Generating...":"Generate AI review"}</button>
          </div>
        </div>
      </aside>
    </div>

    {review&&<section className="card" style={{marginTop:16}}>
      <div className="eyebrow">AI review</div>
      <h2>{review.review_status}</h2>
      <p>{review.case_summary}</p>
      <div className="review-columns">
        <div>
          <h3>Visual findings</h3>
          <div className="list">{review.visual_findings?.length
            ? review.visual_findings.map((f:any,idx:number)=><div className="item" key={idx}><strong>{f.finding}</strong><div className="muted">Evidence {f.evidence_image_id} · {Math.round((f.confidence||0)*100)}%</div></div>)
            : <div className="item muted">No supported visual finding.</div>}
          </div>
        </div>
        <div>
          <h3>Policy evidence</h3>
          {review.policy_reference
            ? <div className="item"><strong>{review.policy_reference.name}</strong><p className="muted">{review.policy_reference.section}</p><p>{review.policy_reference.text}</p></div>
            : <div className="item muted">No matching policy.</div>}
        </div>
      </div>
      <h3>Recommended next action</h3><div className="pill">{review.recommended_action}</div>
      {review.uncertainties?.length>0&&<><h3>Uncertainties</h3><div className="item">{review.uncertainties.join(" · ")}</div></>}
      <h3>Human final decision</h3>
      <div className="actions">
        <button className="btn primary" onClick={()=>decide("APPROVE")}>Approve return</button>
        <button className="btn" onClick={()=>decide("REJECT")}>Reject return</button>
        <button className="btn" onClick={()=>decide("REQUEST_MORE_EVIDENCE")}>Request more evidence</button>
      </div>
    </section>}
  </>;
}
