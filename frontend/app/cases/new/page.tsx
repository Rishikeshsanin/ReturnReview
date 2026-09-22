"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewCase(){
  const router=useRouter();
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);

  async function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();
    setBusy(true);
    setError("");
    const fd=new FormData(e.currentTarget);
    try{
      const row=await api<{id:string}>("/api/cases",{
        method:"POST",
        body:JSON.stringify({
          external_case_id:fd.get("external_case_id"),
          product_name:fd.get("product_name"),
          product_category:"cardboard_box",
          customer_reason:fd.get("customer_reason")
        })
      });
      router.push(`/cases/${row.id}`);
    }catch(e){
      setError(e instanceof Error?e.message:"Could not create case");
    }finally{setBusy(false)}
  }

  return <div className="card" style={{maxWidth:760,margin:"0 auto"}}>
    <div className="eyebrow">New return case</div>
    <h1>Create inspection</h1>
    <p className="muted">MVP currently supports cardboard shipping boxes and visible external damage.</p>
    {error&&<div className="notice error">{error}</div>}
    <form className="form" onSubmit={submit}>
      <div className="two">
        <div className="field"><label>Case / order ID</label><input className="input" name="external_case_id" required placeholder="RR-2026-001"/></div>
        <div className="field"><label>Product</label><input className="input" name="product_name" required defaultValue="Corrugated Shipping Box"/></div>
      </div>
      <div className="field"><label>Category</label><input className="input" value="Cardboard box" disabled/></div>
      <div className="field"><label>Customer return reason</label><textarea className="textarea" name="customer_reason" required placeholder="Describe why the item was returned..."/></div>
      <button className="btn primary" disabled={busy}>{busy?"Creating...":"Create case"}</button>
    </form>
  </div>;
}
