// Screen-space decluttering retains real station locations; never replaces them with invented centroids.
export type ProjectedStation={id:string;x:number;y:number};
export function visibleStationIds(points:ProjectedStation[],width:number,height:number,spacing=32){
 const grid=new Map<string,ProjectedStation[]>(),ids:string[]=[];
 for(const p of points){
  if(p.x<8||p.y<8||p.x>width-8||p.y>height-8)continue;
  const gx=Math.floor(p.x/spacing),gy=Math.floor(p.y/spacing);let overlaps=false;
  for(let x=gx-1;x<=gx+1;x++)for(let y=gy-1;y<=gy+1;y++)
   if((grid.get(`${x}:${y}`)||[]).some(q=>(q.x-p.x)**2+(q.y-p.y)**2<spacing**2))overlaps=true;
  if(overlaps)continue;
  ids.push(p.id);const key=`${gx}:${gy}`;grid.set(key,[...(grid.get(key)||[]),p]);
 }
 return ids;
}
