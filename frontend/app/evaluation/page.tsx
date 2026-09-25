import { api } from "@/lib/api";

function pct(value:number|undefined|null){
  return typeof value==="number" ? `${(value*100).toFixed(1)}%` : "—";
}

export default async function EvaluationPage(){
  let data:any={status:"unavailable"};
  let readiness:any={status:"unavailable",blockers:["api_unavailable"]};
  try{
    [data,readiness]=await Promise.all([
      api<any>("/api/metrics"),
      api<any>("/readiness")
    ]);
  }catch{}

  const llm=data?.llm_review;
  const cv=data?.computer_vision;

  return <>
    <div className="eyebrow">Academic evaluation</div>
    <h1>Evaluation dashboard</h1>

    <div className="card" style={{marginBottom:16}}>
      <div className="section-row"><h2>Production readiness</h2><span className="pill">{readiness.status}</span></div>
      <p className="muted">Readiness reports deployment/configuration state. Metrics below come only from real reviewed evaluation artifacts.</p>
      <div className="list">
        <div className="item"><strong>Persistent evidence</strong><div className="muted">{readiness.database?.durable?"Railway Postgres verified across API redeploy":"not enabled in this deployment"}</div></div>
        <div className="item"><strong>Computer vision</strong><div className="muted">{readiness.cv_ready?`validated lightweight artifacts · ${readiness.cv_model_version}`:"trained artifacts not configured in this deployment"}</div></div>
        <div className="item"><strong>Gemini review</strong><div className="muted">{readiness.llm_ready?`enabled · primary ${readiness.gemini_model}`:"backend Gemini is not enabled"}</div></div>
      </div>
    </div>

    <div className="card" style={{marginBottom:16}}>
      <div className="section-row"><h2>LLM review evaluation</h2><span className="pill">{llm?"human reviewed":"pending"}</span></div>
      {!llm ? <>
        <p className="muted">No human-reviewed Gemini metric artifact is available yet.</p>
      </> : <>
        <p className="muted">Six fixed tool-calling cases were run with <strong>{data.provenance?.model}</strong> and then manually reviewed before these numbers were published.</p>
        <div className="list">
          <div className="item"><strong>Cases</strong><div className="muted">{llm.evaluation_cases}</div></div>
          <div className="item"><strong>Action agreement</strong><div className="muted">{pct(llm.review_action_agreement)}</div></div>
          <div className="item"><strong>Policy correctness</strong><div className="muted">{pct(llm.policy_correctness)}</div></div>
          <div className="item"><strong>Required-tool coverage</strong><div className="muted">{pct(llm.required_tool_coverage)}</div></div>
          <div className="item"><strong>Human correction rate</strong><div className="muted">{pct(llm.human_correction_rate)}</div></div>
          <div className="item"><strong>Unsupported-claim rate</strong><div className="muted">{pct(llm.manual_unsupported_claim_rate)}</div></div>
          <div className="item"><strong>Guard recall on unsupported claims</strong><div className="muted">{pct(llm.grounding_guard_recall_on_unsupported)}</div></div>
          <div className="item"><strong>Average latency</strong><div className="muted">{(llm.average_latency_ms/1000).toFixed(2)} s</div></div>
        </div>
        <p className="muted" style={{marginTop:16}}>The guard recall is the historical result from this recorded run. That review exposed a confidence-arithmetic gap; the current guard now rejects that pattern, while the original metric remains unchanged for auditability.</p>
      </>}
    </div>

    <div className="card">
      <div className="section-row"><h2>Computer vision evaluation</h2><span className="pill">{cv?.segmentation?"public pilot evaluated":"pending"}</span></div>
      {!cv?.segmentation ? <>
        <p className="muted">{cv?.message || "Real held-out CV metrics will appear after training and evaluation."}</p>
        <p className="muted">No placeholder IoU, Dice, F1, or accuracy values are shown.</p>
      </> : <>
        <p className="muted">These are real held-out metrics from the licensed public-data pilot. They are not presented as project-controlled capture results.</p>
        <div className="list">
          <div className="item"><strong>Segmentation mean IoU</strong><div className="muted">{pct(cv.segmentation.mean_iou_all)}</div></div>
          <div className="item"><strong>Segmentation mean Dice</strong><div className="muted">{pct(cv.segmentation.mean_dice_all)}</div></div>
          <div className="item"><strong>Mask mAP@50</strong><div className="muted">{pct(cv.segmentation.mask_map50)}</div></div>
          <div className="item"><strong>Category verification accuracy</strong><div className="muted">{pct(cv.product_verification?.accuracy)}</div></div>
          <div className="item"><strong>Category F1</strong><div className="muted">{pct(cv.product_verification?.f1)}</div></div>
          <div className="item"><strong>Measured CV peak RSS</strong><div className="muted">{typeof cv.runtime?.final_peak_rss_mb==="number"?`${cv.runtime.final_peak_rss_mb.toFixed(0)} MB`:"—"}</div></div>
          <div className="item"><strong>Combined CPU inference</strong><div className="muted">{typeof cv.runtime?.combined_single_image_inference_ms==="number"?`${(cv.runtime.combined_single_image_inference_ms/1000).toFixed(2)} s/image`:"—"}</div></div>
        </div>
      </>}
    </div>
  </>;
}
