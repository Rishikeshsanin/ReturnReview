"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewCase(){
  const router=useRouter();
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [externalId,setExternalId]=useState("");
  const [product,setProduct]=useState("Corrugated Shipping Box");
  const [reason,setReason]=useState("");

  function fillExample(){
    setExternalId(`DEMO-${Date.now().toString().slice(-8)}`);
    setProduct("Corrugated Shipping Box");
    setReason("The shipping box arrived with visible dents and creases on the outside. Please review the photographs to assess the return request.");
    setError("");
  }

  async function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();
    setBusy(true);
    setError("");
    try{
      const row=await api<{id:string}>("/api/cases",{
        method:"POST",
        body:JSON.stringify({
          external_case_id:externalId.trim(),
          product_name:product.trim(),
          product_category:"cardboard_box",
          customer_reason:reason.trim()
        })
      });
      router.push(`/cases/${row.id}`);
    }catch(e){
      setError(e instanceof Error?e.message:"Could not create case");
    }finally{setBusy(false)}
  }

  return <div className="card" style={{maxWidth:860,margin:"0 auto"}}>
    <div className="section-row">
      <div><div className="eyebrow">Step 01 of 04 · New return case</div><h1 className="form-heading">Let's start an inspection</h1></div>
      <span className="pill blue">Cardboard boxes only</span>
    </div>
    <p className="muted">First, describe the return. Next, you'll upload photographs, inspect damage, and review Gemini's evidence-based draft.</p>
    <div className="helper-box" style={{margin:"18px 0 22px"}}>
      <div className="section-row"><div><h3>Presenting this to faculty?</h3><p className="section-subtitle">Pre-fill a realistic sample case. You can edit every field before creating it.</p></div>
      <button type="button" className="btn" onClick={fillExample} disabled={busy}>Fill example details</button></div>
    </div>
    {error&&<div className="notice error" role="alert" style={{marginBottom:18}}>{error}</div>}
    <form className="form" onSubmit={submit}>
      <div className="two">
        <div className="field"><label htmlFor="external_case_id">Case / order ID</label><input id="external_case_id" className="input" name="external_case_id" required maxLength={100} placeholder="e.g. FACULTY-LIVE-03" value={externalId} onChange={e=>setExternalId(e.target.value)} disabled={busy}/><p className="hint">Must be unique for each inspection.</p></div>
        <div className="field"><label htmlFor="product_name">Product name</label><input id="product_name" className="input" name="product_name" required maxLength={160} value={product} onChange={e=>setProduct(e.target.value)} disabled={busy}/><p className="hint">Current MVP supports one category.</p></div>
      </div>
      <div className="field"><label htmlFor="category">Product category</label><input id="category" className="input" value="Cardboard shipping box" disabled/><p className="hint">Fixed for our trained MobileNetV3-Small category verifier.</p></div>
      <div className="field"><label htmlFor="customer_reason">Customer return reason</label><textarea id="customer_reason" className="textarea" name="customer_reason" required maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)} disabled={busy} placeholder="Describe the visible damage reported by the customer..."/><p className="hint">Write only the customer's reported reason; image analysis happens in the next step.</p></div>
      <div className="actions">
        <Link className="btn" href="/">Back to dashboard</Link>
        <button className="btn primary action" type="submit" disabled={busy||!externalId.trim()||!product.trim()||!reason.trim()}>{busy?"Creating case...":"Create case & continue →"}</button>
      </div>
    </form>
  </div>;
}
