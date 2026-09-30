export const BASE = '/api/v1';
let apiKey = '';
export function setApiKey(key:string) { apiKey=key; }
export async function api<T=any>(path:string, options:RequestInit = {}):Promise<T> {
  const response=await fetch(BASE+path,{...options,headers:{'Content-Type':'application/json',...(apiKey?{'X-API-Key':apiKey}:{}),...options.headers}});
  if(!response.ok){let detail;try{detail=(await response.json()).detail}catch{detail=response.statusText}throw new Error(typeof detail==='string'?detail:JSON.stringify(detail))}
  return response.json();
}
export async function downloadReport(kind:string,format:string) {
 const r=await fetch(`${BASE}/reports/${kind}?format=${format}`,{headers:apiKey?{'X-API-Key':apiKey}:{}});
 if(!r.ok)throw new Error('Report could not be generated');
 const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download=`skyguard-${kind}.${format}`;a.click();URL.revokeObjectURL(url);
}
export const labels:Record<string,string>={NORMAL:'Healthy',GENUINE_WEATHER:'Genuine weather',SENSOR_FAULT:'Sensor fault',DATA_COMMS_ISSUE:'Data / comms issue',BOTH_COMPLEX:'Combined event',UNKNOWN_REVIEW:'Needs review'};
export const colors:Record<string,string>={NORMAL:'#04bb8b',GENUINE_WEATHER:'#248fff',SENSOR_FAULT:'#ff4c65',DATA_COMMS_ISSUE:'#849bb7',BOTH_COMPLEX:'#ffab28',UNKNOWN_REVIEW:'#9563ec'};
export const variables=['temperature_c','pressure_hpa','relative_humidity_pct'];
export const variableNames=['Temperature','Atmospheric pressure','Relative humidity'];
export const units=['°C','hPa','%'];
export function date(s:string|undefined){return s?new Date(s).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',hour12:false}):'Awaiting data'}
export function time(s:string|undefined){return s?new Date(s).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'—'}
export function num(n:number|undefined|null,dec=1){return n==null?'—':n.toLocaleString('en-IN',{maximumFractionDigits:dec,minimumFractionDigits:dec})}
export interface Station {id:string;city:string;state:string;latitude:number;longitude:number;elevation_m:number;cadence_seconds:number;pressure_reference:string;network:string;classification:string;root_cause:string;health:number;sensor_health:Record<string,number>;online:boolean;last_update:string;latest:Record<string,number>;evidence_strength:number;decision_stage:string;decision?:any;neighbors?:any[];corrections?:any[]}
export async function downloadData(path:string,filename:string){
 const r=await fetch(BASE+path,{headers:apiKey?{'X-API-Key':apiKey}:{}});
 if(!r.ok){const body=await r.json();throw new Error(body.detail||'Export failed')}
 const url=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=url;a.download=filename;a.click();URL.revokeObjectURL(url);
}
