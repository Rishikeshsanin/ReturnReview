import CaseClient from "@/components/CaseClient";
import { api } from "@/lib/api";

export default async function CasePage({params}:{params:Promise<{id:string}>}){
  const {id}=await params;
  const data=await api<any>(`/api/cases/${id}`);
  return <CaseClient caseId={id} initial={data}/>;
}
