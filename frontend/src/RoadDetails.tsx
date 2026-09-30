import {useEffect, useMemo, useRef, useState} from 'react';
import {useFrame, useThree} from '@react-three/fiber';
import {Html} from '@react-three/drei';
import * as THREE from 'three';

type Way={id:number;geometry?:{lon:number;lat:number}[];tags?:Record<string,string>};
const cache=new Map<string,Way[]>();
let pending:Promise<void>|null=null;
let retryAfter=0;
const plane=new THREE.Plane(new THREE.Vector3(0,0,1),-.445);
const major=new Set(['motorway','trunk','primary','secondary','tertiary']);

// Geographic vectors share the terrain's projection; no replacement basemap.
export default function RoadDetails({onStatus}:{onStatus:(text:string)=>void}){
 const {camera,size,invalidate}=useThree();const [ways,setWays]=useState<Way[]>([]);
 const motion=useRef({signature:'',changed:0,loaded:''});
 const alive=useRef(true);useEffect(()=>{alive.current=true;return ()=>{alive.current=false}},[]);
 useFrame(()=>{
  const zoom=camera.zoom/Math.min(size.width/31,size.height/31);
  const signature=[camera.zoom,...camera.matrixWorld.elements,size.width,size.height].join(',');
  const state=motion.current;
  if(signature!==state.signature){state.signature=signature;state.changed=performance.now();invalidate();return}
  if(zoom<45){if(state.loaded!=='wide'){state.loaded='wide';setWays([]);onStatus('Zoom closer for roads and place names')}return}
  if(performance.now()-state.changed<800){invalidate();return}
  if(pending||Date.now()<retryAfter)return;
  const ray=new THREE.Raycaster(),p=new THREE.Vector3();
  const corners=[[-1,-1],[1,1]].map(([x,y])=>{ray.setFromCamera(new THREE.Vector2(x,y),camera);ray.ray.intersectPlane(plane,p);return [p.x/.92+82,p.y+22]});
  // Quantized bounds avoid repeat downloads for tiny movements; bounded to current close view.
  const step=.025;
  const west=Math.floor(Math.min(corners[0][0],corners[1][0])/step)*step;
  const east=Math.ceil(Math.max(corners[0][0],corners[1][0])/step)*step;
  const south=Math.floor(Math.min(corners[0][1],corners[1][1])/step)*step;
  const north=Math.ceil(Math.max(corners[0][1],corners[1][1])/step)*step;
  if(east-west>1||north-south>1)return;
  const key=[south,west,north,east].map(n=>n.toFixed(3)).join(',');
  if(state.loaded===key)return;
  state.loaded=key;
  if(cache.has(key)){setWays(cache.get(key)!);onStatus('Roads · © OpenStreetMap contributors');return}
  setWays([]);onStatus('Loading roads for this area…');
  const query=`[out:json][timeout:18];way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|service)(_link)?$"](${key});out geom;`;
  pending=fetch('https://overpass-api.de/api/interpreter',{method:'POST',body:new URLSearchParams({data:query}),signal:AbortSignal.timeout(22000)})
   .then(r=>{if(!r.ok)throw Error('Road service unavailable');return r.json()})
   .then(data=>{if(data.remark)throw Error(data.remark);const rows:Way[]=data.elements||[];cache.set(key,rows);if(cache.size>16)cache.delete(cache.keys().next().value!);if(alive.current&&motion.current.loaded===key){setWays(rows);onStatus(rows.length?'Roads · © OpenStreetMap contributors':'No mapped roads in this area')}})
   .catch(()=>{retryAfter=Date.now()+30000;if(alive.current){state.loaded='';onStatus('Road details unavailable · pan or zoom to retry')}})
   .finally(()=>{pending=null;if(alive.current)invalidate()});
 });
 const geometry=useMemo(()=>{
  const main:number[]=[],local:number[]=[];
  for(const way of ways){const points=way.geometry||[],target=major.has(way.tags?.highway||'')?main:local;for(let i=1;i<points.length;i++){for(const p of [points[i-1],points[i]])target.push((p.lon-82)*.92,p.lat-22,.445)}}
  return [main,local].map(points=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points,3));return g});
 },[ways]);
 useEffect(()=>()=>geometry.forEach(g=>g.dispose()),[geometry]);
 const names=useMemo(()=>{const used=new Set<string>();return [...ways].sort((a,b)=>Number(major.has(b.tags?.highway||''))-Number(major.has(a.tags?.highway||''))).filter(w=>{const name=w.tags?.['name:en']||w.tags?.name;if(!name||used.has(name)||!w.geometry?.length)return false;used.add(name);return true}).slice(0,18)},[ways]);
 return <group>
  {geometry.map((g,i)=><lineSegments key={i} geometry={g} renderOrder={3}><lineBasicMaterial color={i?'#dce8cc':'#ffefb2'} transparent opacity={i?.7:.95} toneMapped={false}/></lineSegments>)}
  {names.map(w=>{const p=w.geometry![Math.floor(w.geometry!.length/2)];return <Html key={w.id} position={[(p.lon-82)*.92,p.lat-22,.45]} center zIndexRange={[3,1]} style={{pointerEvents:'none'}}><span className="map-road-name">{w.tags?.['name:en']||w.tags?.name}</span></Html>})}
 </group>;
}
