"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { API, api } from "@/lib/api";

type CaseData = any;
type ZoomImage = {src:string;label:string}|null;
const COMPLETED_CV = ["CV_COMPLETE","GENERATING_REVIEW","READY_FOR_REVIEW","APPROVED","REJECTED","MORE_EVIDENCE_REQUIRED"];
function humanize(value:string){return value.replaceAll("_"," ").toLowerCase().replace(/\b\w/g,c=>c.toUpperCase())}

export default function CaseClient({caseId,initial}:{caseId:string;initial:CaseData}){
  const [data,setData]=useState(initial);
  const [busy,setBusy]=useState("");
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");
  const [reviewSummary,setReviewSummary]=useState(initial.ai_review?.case_summary || "");
  const [reviewerNotes,setReviewerNotes]=useState("");
  const [showOverlays,setShowOverlays]=useState(true);
  const [zoom,setZoom]=useState<ZoomImage>(null);
  const [selectedFile,setSelectedFile]=useState("");

  const review=data.ai_review;
  const findings=data.evidence?.findings || [];
  const status=data.case.status as string;
  const hasCV=COMPLETED_CV.includes(status)||!!data.evidence?.findings?.length;
  const canUpload=["DRAFT","READY_FOR_INSPECTION","MORE_EVIDENCE_REQUIRED","ERROR"].includes(status)&&data.images.length<4;
  const canInspect=status==="READY_FOR_INSPECTION"&&data.images.length>=2;
  const canReview=status==="CV_COMPLETE"||(status==="READY_FOR_REVIEW"&&!review);
  const canDecide=status==="READY_FOR_REVIEW"&&!!review;
  const decided=!!data.human_decision;
  const currentStep=decided?4:review?4:hasCV?3:data.images.length>=2?2:1;
  const isFinished=["APPROVED","REJECTED"].includes(status);

  useEffect(()=>{setReviewSummary(data.ai_review?.case_summary || "")},[data.ai_review?.case_summary]);
  useEffect(()=>{
    if(!zoom)return;
    function onKey(e:KeyboardEvent){if(e.key==="Escape")setZoom(null)}
    document.addEventListener("keydown",onKey);
    return ()=>document.removeEventListener("keydown",onKey);
  },[zoom]);

  async function refresh(){setData(await api(`/api/cases/${caseId}`))}
  async function upload(e:FormEvent<HTMLFormElement>){
    e.preventDefault();
    const formElement=e.currentTarget;
    setBusy("upload");setError("");setNotice("");
    try{
      await api(`/api/cases/${caseId}/images`,{method:"POST",body:new FormData(formElement)});
      await refresh();formElement.reset();setSelectedFile("");
      setNotice("Image added successfully. Upload another view or start inspection when you have at least two.");
    }catch(e){setError(e instanceof Error?e.message:"Upload failed")}
    finally{setBusy("")}
  }
  async function run(path:string,key:string){
    setBusy(key);setError("");setNotice("");
    try{
      await api(path,{method:"POST"});await refresh();
      setNotice(key==="inspect"?"Computer vision inspection completed. Review the damage overlays and move to the Gemini step.":"Review created. Read the evidence and policy before making a human decision.");
    }catch(e){setError(e instanceof Error?e.message:"Operation failed")}
    finally{setBusy("")}
  }
  async function decide(action:string){
    const actionText=action==="APPROVE"?"approve this return":action==="REJECT"?"reject this return":"request more evidence";
    if(!window.confirm(`Confirm that you want to ${actionText}? The decision will be recorded in the audit trail.`))return;
    setBusy(action);setError("");setNotice("");
    try{
      const edited=review&&reviewSummary.trim()!==review.case_summary
        ? {...review,case_summary:reviewSummary.trim()}:null;
      await api(`/api/cases/${caseId}/decision`,{
        method:"POST",body:JSON.stringify({
          action,notes:reviewerNotes.trim()||null,edited_review_json:edited
        })
      });
      await refresh();
      setNotice(`Human decision recorded: ${humanize(action)}. You can verify it in the audit timeline below.`);
    }catch(e){setError(e instanceof Error?e.message:"Decision failed")}
    finally{setBusy("")}
  }
  const statusClass=isFinished?"good":status==="GENERATING_REVIEW"?"warning":"blue";
  return <>
    <div className="section-title">
      <div>
        <div className="eyebrow">Case {data.case.external_case_id} • Interactive inspection</div>
        <h1>{data.case.product_name}</h1>
        <p className="muted">{data.case.customer_reason}</p>
      </div>
      <span className={`pill ${statusClass}`} aria-label={`Case status ${humanize(status)}`}>{humanize(status)}</span>
    </div>

    <div className="workflow-steps" aria-label="Inspection progress">
      {[
        ["Upload photos",`${data.images.length} of 4 views`,data.images.length>=2],
        ["Computer vision","Category + damage",hasCV],
        ["Gemini review","Evidence + policy",!!review],
        ["Human decision","Final authority",decided]
      ].map(([title,subtitle,complete],idx)=><div key={idx} className={`workflow-step ${complete?"done":currentStep===idx+1?"active":""}`}>
        <span className="step-number">{complete?"✓":idx+1}</span>
        <div><strong>{title}</strong><small>{subtitle}</small></div>
      </div>)}
    </div>

    {error&&<div className="notice error" role="alert" style={{marginBottom:18}}>{error}</div>}
    {notice&&<div className="notice success" role="status" style={{marginBottom:18}}>{notice}</div>}
    {isFinished&&<div className="notice success" style={{marginBottom:18}}>
      <strong>Inspection complete.</strong> The reviewer decision and evidence are saved. To demonstrate another case, <Link href="/cases/new" style={{textDecoration:"underline",fontWeight:800}}>start a new inspection</Link>.
    </div>}
    {status==="GENERATING_REVIEW"&&<div className="notice" style={{marginBottom:18}}>
      <strong>Gemini request in progress.</strong> Review generation can be slower during provider outages. Refresh the page to check for a saved review; if this remains stuck after an interrupted backend restart, a maintainer must safely recover the case status.
    </div>}

    <div className="result-grid">
      <section className="card" aria-labelledby="evidence-title">
        <div className="section-row"><div><div className="eyebrow">Step 01 • Evidence</div><h2 id="evidence-title">Visual evidence</h2></div><span className="pill blue">{data.images.length}/4 images</span></div>
        <p className="section-subtitle">Upload two to four different views of the <strong>same cardboard box</strong>. Each image stays linked to its inspection findings.</p>
        {data.images.length===0?
          <div className="evidence"><div><h3 style={{color:"#fff"}}>Your box photos will appear here</h3><p>Choose a front, side or top photograph below to begin.</p></div></div>:
          <div className="image-grid">{data.images.map((i:any)=><figure className="image-card" key={i.id}>
            <button type="button" className="image-zoom" onClick={()=>setZoom({src:`${API}${i.image_url}`,label:`${humanize(i.view_label)} view`})} aria-label={`Enlarge ${i.view_label} photograph`}>
              <img src={`${API}${i.image_url}`} alt={`${i.view_label} view of returned cardboard box`}/>
            </button>
            <figcaption><strong>{humanize(i.view_label)} view</strong><span>Quality {typeof i.quality_score==="number"?Math.round(i.quality_score*100)+"%":"n/a"}</span></figcaption>
            {i.quality_warning&&<small className="warn">{i.quality_warning}</small>}
          </figure>)}</div>}

        {canUpload?
          <form className="form helper-box" onSubmit={upload} style={{marginTop:20}}>
            <div className="section-row"><h3>Add another image</h3><span className="pill blue">{data.images.length}/4 uploaded</span></div>
            <div className="two">
              <div className="field"><label htmlFor="photo-upload">Select an image</label><input id="photo-upload" className="input" type="file" name="image" accept="image/jpeg,image/png,image/webp" required disabled={!!busy} onChange={e=>setSelectedFile(e.target.files?.[0]?.name||"")}/></div>
              <div className="field"><label htmlFor="view-label">Which side of the box?</label><select id="view-label" className="select" name="view_label" defaultValue="front" disabled={!!busy}>
                <option value="front">Front view</option><option value="back">Back view</option><option value="left">Left view</option><option value="right">Right view</option><option value="top">Top view</option><option value="bottom">Bottom view</option>
              </select></div>
            </div>
            {selectedFile&&<span className="section-subtitle">Selected: <strong>{selectedFile}</strong></span>}
            <button className="btn primary action block" type="submit" disabled={!!busy}>{busy==="upload"?"Uploading image...":"+ Add image to this case"}</button>
            <span className="section-subtitle">JPEG, PNG or WebP; maximum 4 views. Use distinct angles rather than reuploading the same picture.</span>
          </form>:
          <div className="notice" style={{marginTop:20}}>
            {isFinished?"This case is complete; evidence is preserved as part of the audit.":"Image uploads are locked during this workflow stage."}
          </div>}

        {hasCV&&<div style={{marginTop:25}}>
          <div className="section-row"><div><div className="eyebrow">Step 02 • Computer vision</div><h2>Detected regions</h2></div><span className="pill blue">{findings.length} findings</span></div>
          <p className="section-subtitle">Segmentation masks are model predictions—not guaranteed ground truth. Compare them with the original photographs.</p>
          {findings.length>0?<>
            <div className="actions" style={{margin:"14px 0"}}>
              <button className={`btn ${showOverlays?"primary":""}`} type="button" onClick={()=>setShowOverlays(true)} aria-pressed={showOverlays}>Show AI masks</button>
              <button className={`btn ${!showOverlays?"primary":""}`} type="button" onClick={()=>setShowOverlays(false)} aria-pressed={!showOverlays}>Compare original photos</button>
            </div>
            <div className="image-grid">{findings.map((f:any)=>{
              const source=data.images.find((i:any)=>i.id===f.image_id);
              const src=(!showOverlays&&source)?`${API}${source.image_url}`:f.mask_url?`${API}${f.mask_url}`:f.mask_path?`${API}/media/${f.mask_path}`:source?`${API}${source.image_url}`:"";
              return <figure className="image-card" key={f.finding_id}>
                {src?<button type="button" className="image-zoom" onClick={()=>setZoom({src,label:`${humanize(f.defect_type)} — ${showOverlays?"AI overlay":"original image"}`})} aria-label={`Enlarge ${f.defect_type} ${showOverlays?"overlay":"original"}`}>
                  <img src={src} alt={`${showOverlays?"AI damage overlay":"Original photo"} for ${f.defect_type}`}/>
                </button>:<div className="evidence small">Overlay unavailable</div>}
                <figcaption><strong>{humanize(f.defect_type)}</strong><span>{Math.round((f.confidence||0)*100)}% model confidence</span></figcaption>
                <small className="muted">Predicted affected image area: {typeof f.affected_area_percent==="number"?f.affected_area_percent.toFixed(2):"n/a"}%</small>
              </figure>;
            })}</div>
          </>:<div className="helper-box">No supported visible-damage region was predicted. That does not establish that the item is undamaged.</div>}
        </div>}
      </section>

      <aside className="card" aria-label="Inspection actions">
        <div className="eyebrow">Guided experience</div><h2>What happens next?</h2>
        <div className={`workflow-card ${canInspect?"active":hasCV?"complete":""}`}>
          <div><span className="step">02</span><strong className="big-label">Run computer vision</strong></div>
          <p className="section-subtitle">MobileNetV3-Small checks the box category; YOLO11n-seg identifies visible-damage regions.</p>
          <button className="btn primary action" disabled={!!busy||!canInspect} onClick={()=>run(`/api/cases/${caseId}/inspect`,"inspect")}>{busy==="inspect"?"Inspecting images...":hasCV?"Inspection complete ✓":"Run CV inspection →"}</button>
          <span className="workflow-help">{data.images.length<2?"Upload at least 2 different views to unlock this step.":canInspect?"Your images are ready. Run the trained CV models.":hasCV?"CV evidence was saved for this case.":"Available after image upload."}</span>
        </div>
        <div className={`workflow-card ${canReview?"active":review?"complete":""}`}>
          <div><span className="step">03</span><strong className="big-label">Generate grounded review</strong></div>
          <p className="section-subtitle">Gemini calls the case, visual-evidence, and policy tools. Structured output passes through a deterministic guard.</p>
          <button className="btn primary action" disabled={!!busy||!canReview} onClick={()=>run(`/api/cases/${caseId}/ai-review`,"review")}>{busy==="review"?"Generating review...":review?"Review generated ✓":"Generate Gemini review →"}</button>
          <span className="workflow-help">{review?"Read the review below before deciding.":canReview?"The CV evidence is ready for an evidence-grounded draft.":"Complete CV inspection first."}</span>
        </div>
        <div className="helper-box" style={{marginTop:16}}>
          <h3>Human authority</h3>
          <p className="section-subtitle">The AI never approves or rejects a return. A reviewer makes and records that final decision.</p>
        </div>
      </aside>
    </div>

    {review&&<section className="card" style={{marginTop:20}} aria-labelledby="review-title">
      <div className="section-row">
        <div><div className="eyebrow">Step 03 • Gemini + policy</div><h2 id="review-title">Evidence-grounded AI review</h2></div>
        <span className="pill blue">{humanize(review.recommended_action)}</span>
      </div>
      <div className="review-summary"><strong>Review status: </strong>{humanize(review.review_status)}</div>
      <div className="field">
        <label htmlFor="review-summary">Case summary <span className="muted" style={{fontWeight:500}}>— editable by the reviewer</span></label>
        <textarea id="review-summary" className="textarea" value={reviewSummary} onChange={e=>setReviewSummary(e.target.value)} disabled={!canDecide}/>
      </div>
      <div className="review-columns" style={{marginTop:22}}>
        <div>
          <h3>Evidence-backed findings</h3>
          <div className="list">{review.visual_findings?.length
            ? review.visual_findings.map((f:any,idx:number)=><div className="item" key={idx}><strong>{f.finding}</strong><div className="section-subtitle">Evidence image: {f.evidence_image_id} • {Math.round((f.confidence||0)*100)}% confidence</div></div>)
            : <div className="item muted">No supported visual finding.</div>}</div>
        </div>
        <div>
          <h3>Retrieved policy</h3>
          {review.policy_reference?<div className="item"><strong>{review.policy_reference.name}</strong><p className="muted">{review.policy_reference.section} · {review.policy_reference.policy_id}</p><p>{review.policy_reference.text}</p></div>
          :<div className="item muted">No matching policy was found.</div>}
        </div>
      </div>
      <div className="helper-box" style={{marginTop:20}}>
        <strong>Recommended action:</strong> {humanize(review.recommended_action)}.
        {review.uncertainties?.length>0&&<><h3>Uncertainties</h3><p>{review.uncertainties.join(" · ")}</p></>}
      </div>
      {review.unsupported_claims_detected&&<div className="notice error" role="alert" style={{marginTop:14}}>Grounding guard flagged unsupported content. Review carefully before making a decision.</div>}
      <div style={{marginTop:28}}>
        <div className="eyebrow">Step 04 • Human-in-the-loop</div>
        <h2>Final reviewer decision</h2>
        <p className="section-subtitle">Check the original images, masks, policy and AI draft. The human—not Gemini—decides how to proceed.</p>
        <div className="field" style={{marginBottom:16}}>
          <label htmlFor="reviewer-notes">Reviewer notes (optional)</label>
          <textarea id="reviewer-notes" className="textarea" value={reviewerNotes} onChange={e=>setReviewerNotes(e.target.value)} placeholder="Explain what evidence supports your choice, or what additional information is needed..." disabled={!canDecide}/>
        </div>
        <div className="actions">
          <button className="btn success action" disabled={!!busy||!canDecide} onClick={()=>decide("APPROVE")}>✓ Approve return</button>
          <button className="btn danger action" disabled={!!busy||!canDecide} onClick={()=>decide("REJECT")}>Reject return</button>
          <button className="btn action" disabled={!!busy||!canDecide} onClick={()=>decide("REQUEST_MORE_EVIDENCE")}>Request more evidence</button>
        </div>
        <span className="workflow-help">You'll be asked to confirm before recording a final decision.</span>
        {data.human_decision&&<div className="notice success" style={{marginTop:17}}>Recorded human decision: <strong>{humanize(data.human_decision)}</strong></div>}
      </div>
    </section>}

    <section className="card" style={{marginTop:20}}>
      <div className="section-row"><div><div className="eyebrow">Evidence trail</div><h2>Audit timeline</h2></div><span className="pill blue">{data.timeline?.length||0} events</span></div>
      <p className="section-subtitle">Actions are stored with the return case, so the decision can be reviewed later.</p>
      <div className="list">{(data.timeline||[]).length?
        data.timeline.map((e:any)=><div className="item timeline-item" key={e.id}><span className="timeline-dot" aria-hidden="true"/><div><strong>{humanize(e.event_type)}</strong><div className="muted">{new Date(e.created_at).toLocaleString("en-IN")}</div></div></div>):
        <div className="muted">No audit events recorded yet.</div>}
      </div>
    </section>

    {zoom&&<div className="lightbox-backdrop" onMouseDown={()=>setZoom(null)} role="presentation">
      <div className="lightbox-panel" role="dialog" aria-modal="true" aria-label={zoom.label} onMouseDown={e=>e.stopPropagation()}>
        <div className="section-row"><strong>{zoom.label}</strong><button type="button" className="btn" onClick={()=>setZoom(null)}>Close image ×</button></div>
        <img src={zoom.src} alt={zoom.label}/>
      </div>
    </div>}
  </>;
}
