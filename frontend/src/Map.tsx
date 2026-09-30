import { Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, Component, type ReactNode } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { Plus, Minus, RotateCcw, Layers, Navigation } from 'lucide-react';
import { colors, labels, num, type Station } from './api';
import {visibleStationIds} from './mapVisibility';

import RoadDetails from './RoadDetails';
type Props={stations:Station[];selected?:string;onSelect:(id:string)=>void;onOpen?:(id:string)=>void;compact?:boolean};
const project=(lon:number,lat:number):[number,number]=>[(lon-82)*.92,lat-22];
const greens=['#62886f','#548372','#679579','#608d7a','#718d72','#648f6e','#759080','#557e69'];
const geography=fetch('/india-states.geojson').then(r=>{if(!r.ok)throw Error('Map unavailable');return r.json()});
const terrainCache=new WeakMap<object,any[]>();
function terrain(geo:any){
 let cached=terrainCache.get(geo);if(cached)return cached;
 cached=geo.features.flatMap((f:any,i:number)=>f.geometry.coordinates.map((rings:number[][][],j:number)=>{
  if(rings[0].length<4)return null;
  const shape=new THREE.Shape(rings[0].map(p=>new THREE.Vector2(...project(p[0],p[1]))));
  for(const hole of rings.slice(1))shape.holes.push(new THREE.Path(hole.map(p=>new THREE.Vector2(...project(p[0],p[1])))));
  return {geometry:new THREE.ExtrudeGeometry(shape,{depth:.38,bevelEnabled:true,bevelThickness:.05,bevelSize:.025,bevelSegments:1}),key:`${i}-${j}`,name:f.properties.NAME_1,color:greens[i%greens.length],line:rings[0].map(p=>[...project(p[0],p[1]),.44] as [number,number,number])};
 }).filter(Boolean));terrainCache.set(geo,cached!);return cached!;
}
const scales:Record<string,{min:number;max:number;unit:string;label:string}>={temperature_c:{min:0,max:45,unit:'°C',label:'Temperature'},pressure_hpa:{min:995,max:1025,unit:'hPa',label:'MSL pressure'},relative_humidity_pct:{min:0,max:100,unit:'%',label:'Humidity'}};
function stationColor(st:Station,layer:string){
 if(layer==='health')return st.health<70?'#ff5266':st.health<90?'#ffb629':'#00d2a2';
 const scale=scales[layer];if(!scale)return colors[st.classification]||'#aab9ce';
 const value=(st.latest as any)?.[layer];if(value==null)return '#aab9ce';
 return new THREE.Color().setHSL(.64*(1-Math.min(1,Math.max(0,(value-scale.min)/(scale.max-scale.min)))),.85,.52).getStyle();
}
// Farthest-point ordering provides a stable, spatially spread prefix at every zoom level.
function spreadStations(stations:Station[]){
 const pending=[...stations].sort((a,b)=>a.id.localeCompare(b.id)),ordered:Station[]=[];
 const distances=new Map(pending.map(s=>[s.id,Infinity]));
 while(pending.length){
  let best=0;for(let i=1;i<pending.length;i++)if(distances.get(pending[i].id)!>distances.get(pending[best].id)!)best=i;
  const st=pending.splice(best,1)[0];ordered.push(st);
  for(const other of pending){const dx=(other.longitude-st.longitude)*.92,dy=other.latitude-st.latitude;distances.set(other.id,Math.min(distances.get(other.id)!,dx*dx+dy*dy))}
 }
 return ordered;
}
const pinGeometry=new THREE.CircleGeometry(.21,20);
function Neighbors(){
 const [geo,setGeo]=useState<any>(null);
 useEffect(()=>{fetch('/neighbor-countries.geojson').then(r=>r.json()).then(setGeo).catch(()=>{})},[]);
 const outlines=useMemo(()=>geo?.features.flatMap((f:any)=>{
  const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;
  return polys.map((p:number[][][],i:number)=>({key:f.properties.name+i,points:p[0].map(c=>[...project(c[0],c[1]),-.12] as [number,number,number])}));
 }),[geo]);
 return <group>{outlines?.map((o:any)=><Line key={o.key} points={o.points} color="#719eac" lineWidth={.9} transparent opacity={.35}/>)}</group>;
}
function VisibleCountry(props:Props&{geo:any;layer:string;viewZoom:number;onCount:(n:number)=>void}){
 const {camera,size}=useThree();const [ids,setIds]=useState<string[]>([]);const signature=useRef('');
 const ordered=useMemo(()=>{const spread=spreadStations(props.stations);const priority=[spread.find(s=>s.id===props.selected),...Object.keys(labels).map(k=>spread.find(s=>s.classification===k))].filter(Boolean) as Station[];return [...new Map([...priority,...spread].map(s=>[s.id,s])).values()]},[props.stations,props.selected]);
 const previous=useRef('');
 useFrame(()=>{
  const key=[camera.zoom,size.width,size.height,...camera.matrixWorld.elements,ordered.map(s=>s.id).join(',')].join('|');
  if(signature.current===key)return;signature.current=key;
  const points=ordered.map(st=>{const [x,y]=project(st.longitude,st.latitude);const p=new THREE.Vector3(x,y,props.viewZoom>10?.46:.72).project(camera);return {id:st.id,x:(p.x+1)*size.width/2,y:(1-p.y)*size.height/2}});
  const next=visibleStationIds(points,size.width,size.height,32),idKey=next.join('|');
  if(previous.current!==idKey){previous.current=idKey;setIds(next);props.onCount(next.length)}
 });
 const visible=useMemo(()=>{const set=new Set(ids);return ordered.filter(s=>set.has(s.id))},[ids,ordered]);
 return <Country {...props} stations={visible}/>;
}
function Country({geo,stations,selected,onSelect,onOpen,layer,viewZoom}:{geo:any}&Props&{layer:string;viewZoom:number}){
 const polygons=useMemo(()=>terrain(geo),[geo]);
 const stateLabels=useMemo(()=>{const groups=new Map<string,any>();for(const p of polygons){p.geometry.computeBoundingBox();const box=p.geometry.boundingBox;const area=(box.max.x-box.min.x)*(box.max.y-box.min.y);if(!groups.has(p.name)||groups.get(p.name).area<area)groups.set(p.name,{name:p.name,area,x:(box.min.x+box.max.x)/2,y:(box.min.y+box.max.y)/2})}return [...groups.values()]},[polygons]);
 const [hover,setHover]=useState<string|null>(null),[hoveredStation,setHoveredStation]=useState<string|null>(null);
 const dots=useRef<THREE.InstancedMesh>(null),rings=useRef<THREE.InstancedMesh>(null);
 const {invalidate}=useThree();
 useEffect(()=>()=>{document.body.style.cursor='auto'},[]);
 useLayoutEffect(()=>{
  const matrix=new THREE.Matrix4(),color=new THREE.Color();
  stations.forEach((st,i)=>{const [x,y]=project(st.longitude,st.latitude),size=(st.id===selected?1.25:1)/Math.max(1,viewZoom*.7);
   matrix.makeScale(size,size,size);matrix.setPosition(x,y,viewZoom>10?.46:.72);dots.current!.setMatrixAt(i,matrix);dots.current!.setColorAt(i,color.set(stationColor(st,layer)));
   matrix.makeScale(size*1.16,size*1.16,size);matrix.setPosition(x,y,viewZoom>10?.455:.69);rings.current!.setMatrixAt(i,matrix);
  });
  for(const mesh of [dots.current!,rings.current!]){mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere()}
  if(dots.current!.instanceColor)dots.current!.instanceColor.needsUpdate=true;invalidate();
 },[stations,selected,layer,viewZoom,invalidate]);
 const active=stations.find(st=>st.id===selected),preview=stations.find(st=>st.id===hoveredStation&&st.id!==selected),scale=scales[layer];
 return <group>
  {polygons.map((p:any)=><group key={p.key}><mesh geometry={p.geometry} dispose={null} onPointerOver={e=>{e.stopPropagation();setHover(p.name)}} onPointerOut={()=>setHover(null)}><meshStandardMaterial color={hover===p.name?'#a3cbb0':p.color} roughness={.85} metalness={.08}/></mesh><Line points={p.line} color={hover===p.name?'#ffffff':'#d0ebd9'} lineWidth={hover===p.name?1.5:.7} transparent opacity={.8}/></group>)}
  <instancedMesh key={`rings-${stations.length}`} ref={rings} args={[pinGeometry,undefined,stations.length]}><meshBasicMaterial toneMapped={false} color="white" side={THREE.DoubleSide}/></instancedMesh>
  <instancedMesh key={`dots-${stations.length}`} ref={dots} args={[pinGeometry,undefined,stations.length]} onClick={e=>{e.stopPropagation();if(e.delta<4&&e.instanceId!=null)onSelect(stations[e.instanceId].id)}} onPointerOver={e=>{e.stopPropagation();document.body.style.cursor='pointer';if(e.instanceId!=null)setHoveredStation(stations[e.instanceId].id)}} onPointerOut={()=>{document.body.style.cursor='auto';setHoveredStation(null)}}><meshBasicMaterial side={THREE.DoubleSide} toneMapped={false}/></instancedMesh>
  {viewZoom>=1.6&&viewZoom<15&&stateLabels.map(p=><Html key={p.name} position={[p.x,p.y,.58]} center style={{pointerEvents:'none'}} zIndexRange={[2,0]}><span className="map-region-name">{p.name}</span></Html>)}
  {hover&&viewZoom<15&&<Html position={[0,14,.7]} center style={{pointerEvents:'none'}}><span className="map-state-label">{hover}</span></Html>}
  {preview&&<Html position={[...project(preview.longitude,preview.latitude),viewZoom>10?.48:1.3]} center style={{pointerEvents:'none'}} zIndexRange={[9,0]}><span className="map-state-label">{preview.city} · {scale?`${num((preview.latest as any)?.[layer])} ${scale.unit}`:labels[preview.classification]}</span></Html>}
  {active&&<Html wrapperClass="station-card-anchor" position={[...project(active.longitude,active.latitude),viewZoom>10?.48:1.8]} center zIndexRange={[60,50]} calculatePosition={(el,camera,size)=>{const p=new THREE.Vector3().setFromMatrixPosition(el.matrixWorld).project(camera);return [Math.max(125,Math.min(size.width-125,(p.x+1)*size.width/2)),Math.max(150,Math.min(size.height-180,(1-p.y)*size.height/2))]}}><button className="map-pin-label" aria-label={`Open station report for ${active.id}`} onClick={()=>onOpen?.(active.id)} disabled={!onOpen}><span className="status-dot" style={{background:stationColor(active,layer)}}/>{active.id}<small>{active.city} · {labels[active.classification]||'Needs review'}</small><small>Open station report →</small></button></Html>}
 </group>
}
function CameraControl({zoom,reset,onZoom}:{zoom:number;reset:number;onZoom:(ratio:number)=>void}){
 const {camera,size,invalidate}=useThree();const controls=useRef<any>(null);
 const base=Math.min(size.width/31,size.height/31);
 useEffect(()=>{camera.position.set(0,-14,42);camera.lookAt(0,0,0);if(controls.current)controls.current.target.set(0,0,0);invalidate()},[reset,camera,invalidate]);
 useEffect(()=>{if(camera instanceof THREE.OrthographicCamera){camera.zoom=base*zoom;camera.updateProjectionMatrix();onZoom(zoom);invalidate()}},[zoom,base,camera,invalidate,onZoom,reset]);
 // Fixed tilt: pan and zoom remain available, but no gesture can expose the underside.
 return <OrbitControls ref={controls} zoomToCursor enablePan screenSpacePanning enableRotate={false} mouseButtons={{LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.PAN}} touches={{ONE:THREE.TOUCH.PAN,TWO:THREE.TOUCH.DOLLY_PAN}} minZoom={base*.6} maxZoom={base*180} enableDamping dampingFactor={.1} onChange={()=>onZoom(camera.zoom/base)} target={[0,0,0]}/>;
}
class MapBoundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true}}render(){return this.state.failed?this.props.fallback:this.props.children}}
function FlatMap({geo,stations,onSelect,layer,onCount}:Props&{geo:any;layer:string;onCount:(n:number)=>void}){useEffect(()=>onCount(stations.length),[stations.length,onCount]);return <svg viewBox="-16 -17 34 34" className="flat-map" aria-label="India AWS network"><g transform="scale(1,-1)">{geo.features.map((f:any,i:number)=><path key={i} d={f.geometry.coordinates.map((poly:number[][][])=>poly.map(r=>r.map((p,j)=>`${j?'L':'M'}${project(p[0],p[1]).join(' ')}`).join(' ')+'Z').join(' ')).join(' ')} fill={greens[i%greens.length]} stroke="#d9efe4" strokeWidth=".035"/>)}{stations.map(s=><circle key={s.id} cx={project(s.longitude,s.latitude)[0]} cy={project(s.longitude,s.latitude)[1]} r=".2" fill={stationColor(s,layer)} stroke="white" strokeWidth=".06" role="button" tabIndex={0} aria-label={s.city} onClick={()=>onSelect(s.id)} onKeyDown={e=>{if(e.key==='Enter')onSelect(s.id)}}/>)}</g></svg>}
export default function IndiaMap(props:Props){
 const [geo,setGeo]=useState<any>(null),[zoom,setZoom]=useState(1),[reset,setReset]=useState(0),[layer,setLayer]=useState('status'),[error,setError]=useState('');
 const [viewZoom,setViewZoom]=useState(1),[visibleCount,setVisibleCount]=useState(0),[roadStatus,setRoadStatus]=useState('Zoom closer for roads and place names');
 const onZoom=useCallback((ratio:number)=>setViewZoom(v=>Math.abs(v-ratio)>.025?ratio:v),[]);
 useEffect(()=>{geography.then(setGeo).catch(()=>setError('Map unavailable. Station list remains available.'))},[]);
 return <div className={`india-map ${viewZoom>10?'local-detail':''} ${props.compact?'compact':''}`}>
  <div className="map-top"><span className="map-caption"><span className="status-dot"/> NATIONAL NETWORK <span className="map-caption-light">/ INDIA</span></span><label className="layer-picker"><Layers size={15}/><select aria-label="Map layer" value={layer} onChange={e=>setLayer(e.target.value)}><option value="status">AWS status</option><option value="temperature_c">Temperature</option><option value="pressure_hpa">Pressure</option><option value="relative_humidity_pct">Humidity</option><option value="health">Sensor health</option></select></label></div>
  <span className="country-label pakistan">PAKISTAN</span><span className="country-label china">CHINA</span><span className="country-label nepal">NEPAL</span><span className="country-label sea">ARABIAN<br/>SEA</span><span className="country-label bay">BAY OF<br/>BENGAL</span><span className="country-label ocean">INDIAN OCEAN</span>
  {geo?<MapBoundary fallback={<FlatMap {...props} geo={geo} layer={layer} onCount={setVisibleCount}/>}><Canvas frameloop="demand" dpr={[1,1.5]} orthographic camera={{position:[0,-14,42],zoom:18,near:.1,far:100}} gl={{antialias:true,alpha:true}}>
   <ambientLight intensity={1.6}/><directionalLight position={[-12,15,30]} intensity={2.5}/><directionalLight position={[10,-10,20]} color="#b0e9ff" intensity={1}/>
   <Suspense fallback={null}><Neighbors/><VisibleCountry {...props} geo={geo} layer={layer} viewZoom={viewZoom} onCount={setVisibleCount}/><RoadDetails onStatus={setRoadStatus}/></Suspense><CameraControl zoom={zoom} reset={reset} onZoom={onZoom}/>
  </Canvas></MapBoundary>:<div className="map-loading">{error||'Loading national network…'}</div>}
  <div className="map-controls"><button aria-label="Zoom in" onClick={()=>setZoom(Math.min(180,viewZoom*1.6))}><Plus size={19}/></button><button aria-label="Zoom out" onClick={()=>setZoom(Math.max(.6,viewZoom/1.6))}><Minus size={19}/></button><button aria-label="Reset map" onClick={()=>{setZoom(1);setReset(reset+1)}}><RotateCcw size={17}/></button></div>
  <div className="compass">N<Navigation size={22}/></div>
  <div className="map-legend">{layer==='status'?['NORMAL','GENUINE_WEATHER','SENSOR_FAULT','DATA_COMMS_ISSUE','UNKNOWN_REVIEW'].map(k=><span key={k}><i style={{background:colors[k]}}/>{labels[k]}</span>):layer==='health'?<span>Sensor health · green ≥90 / amber ≥70 / red &lt;70</span>:<span>{scales[layer].label} · {scales[layer].min} <i style={{width:85,borderRadius:3,background:'linear-gradient(90deg,#1d48ed,#19d8ae,#c6e819,#ee241c)'}}/> {scales[layer].max} {scales[layer].unit} · gray: no data</span>}</div>
  <span className="map-credit">{visibleCount} / {props.stations.length} dots in view · drag to pan, zoom for more · Neighbor outlines: Natural Earth · {roadStatus}{viewZoom>=45&&<> · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OSM attribution</a></>}</span>
 </div>
}
