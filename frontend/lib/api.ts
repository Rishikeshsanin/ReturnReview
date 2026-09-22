export const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://returnreview-api-production.up.railway.app";

export async function api<T>(path:string, init?:RequestInit):Promise<T>{
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers:{
      ...(init?.body instanceof FormData ? {} : {"Content-Type":"application/json"}),
      ...(init?.headers||{})
    },
    cache:"no-store"
  });
  if(!res.ok){
    let message=`Request failed (${res.status})`;
    try{const body=await res.json();message=body.detail||message}catch{}
    throw new Error(message);
  }
  return res.json();
}
