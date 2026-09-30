import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import {resolvePresentationFont,applyPresentationChartFont,finalizePresentation} from '/Users/bhavesh/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations/container_tools/artifact_tool_utils.mjs';
const req=createRequire('/Users/bhavesh/Downloads/26073/frontend/package.json');
const React=req('react'),{renderToStaticMarkup}=req('react-dom/server'),icons=req('lucide-react');
const ROOT='/Users/bhavesh/Downloads/26073',DIR=path.join(ROOT,'docs/presentation/redesign/build');
const SKILL='/Users/bhavesh/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const P=Presentation.create({slideSize:{width:1280,height:720}});
const FONT=resolvePresentationFont({fontFamily:'Arial'});
const C={ink:'#17324D',muted:'#52667B',blue:'#193C56',teal:'#168B83',amber:'#D69A24',paleBlue:'#EEF5FD',paleTeal:'#EDF8F5',paleAmber:'#FFF7E6',line:'#CDDBE8',white:'#FFFFFF'};
const sih=new Uint8Array(await fs.readFile(path.join(DIR,'sih.png')));
function shape(s,x,y,w,h,fill=C.white,stroke=C.line,geometry='roundRect'){return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:1.6},borderRadius:geometry==='roundRect'?16:0});}
function text(s,t,x,y,w,h=50,size=22,bold=false,color=C.ink,align='left') {const a=shape(s,x,y,w,h,'none','none','textbox');a.text=t;a.text.style={typeface:FONT,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',autoFit:'none',insets:{top:0,left:0,right:0,bottom:0}};return a;}
function icon(s,name,x,y,size=34,color=C.blue){const svg=renderToStaticMarkup(React.createElement(icons[name],{size:64,color,strokeWidth:1.8}));return s.images.add({blob:new TextEncoder().encode(svg),contentType:'image/svg+xml',alt:name,position:{left:x,top:y,width:size,height:size},fit:'contain'});}
function connect(s,a,b,color=C.blue,from='right',to='left',kind='straight'){return s.shapes.connect(a,b,{fromSide:from,toSide:to,kind,line:{fill:color,width:2.2},tail:{type:'triangle',width:'sm',length:'sm'}});}
function box(s,x,y,w,h,title,body,color=C.blue,fill=C.paleBlue,ico){const a=shape(s,x,y,w,h,fill,color);if(ico)icon(s,ico,x+18,y+18,30,color);text(s,title,x+(ico?60:20),y+19,w-(ico?78:40),48,w<220?20:22,true);if(body)text(s,body,x+20,y+62,w-40,h-66,w<280?18:20,false,C.muted);return a;}
function header(title,n,subtitle){const s=P.slides.add();s.background.fill=C.white;text(s,'OFF BY ONE',44,27,190,27,18,true,C.blue);text(s,title,250,22,800,52,32,true);s.images.add({blob:sih,contentType:'image/png',alt:'Smart India Hackathon 2026',fit:'contain',position:{left:1085,top:15,width:150,height:72}});shape(s,44,94,1192,2,C.line,'none','rect');if(subtitle)text(s,subtitle,44,112,1185,42,22,false,C.muted);shape(s,0,682,1280,38,C.blue,'none','rect');text(s,'SKYGUARD  /  SIH26073',44,693,700,20,14,true,C.white);text(s,String(n).padStart(2,'0'),1185,690,50,24,18,true,C.white,'right');return s;}
function note(s,t){s.speakerNotes.textFrame.setText(t);}

function block(s,x,y,w,h,title,body,ic,col=C.teal){
 const a=shape(s,x,y,w,h,C.white,col);
 shape(s,x+10,y+10,w-20,38,col===C.teal?C.paleTeal:C.paleAmber,'none');
 text(s,title,x+20,y+17,w-40,30,21,true,C.ink,'center');
 icon(s,ic,x+w/2-27,y+62,54,col);
 text(s,body,x+18,y+130,w-36,h-138,19,false,C.ink,'center');return a;
}
{
 const s=header('SKYGUARD',1);
 text(s,'Understanding unusual\nweather readings',54,164,760,125,49,true);
 text(s,'AI/ML-Based Intelligent Anomaly Detection\nfor Automatic Weather Stations (AWS)',57,319,750,76,26,false,C.muted);
 icon(s,'ShieldCheck',966,181,170,C.teal);
 text(s,'Temperature',54,463,190,34,23,true);text(s,'Pressure',292,463,190,34,23,true);text(s,'Humidity',530,463,190,34,23,true);
 icon(s,'Thermometer',54,414,33,C.teal);icon(s,'Gauge',292,414,33,C.teal);icon(s,'Droplets',530,414,33,C.teal);
 text(s,'SIH26073',54,555,235,38,29,true,C.teal);
 text(s,'Disaster Management / Software\nOFF BY ONE / Team ID 132195',54,608,680,58,20,false,C.muted);
 text(s,'A working prototype\n500 simulated stations',906,442,310,83,25,true,C.ink,'center');
 note(s,'Official PS and user team details from linked source Canva deck. Synthetic prototype, no live IMD feed.');
}
{
 const s=header('PROPOSED SOLUTION',2,'An unusual reading needs an explanation before an operator can act.');
 const a=block(s,44,251,232,276,'AWS reading','Noisy, missing or\nunusually high / low','RadioTower',C.blue);
 const b=block(s,342,185,270,192,'Station history','Spikes, drift and stuck values','History');
 const c=block(s,342,423,270,192,'Virtual Buddy','Trusted nearby stations\nadd weather context','Network');
 const d=block(s,677,282,254,257,'Evidence fusion','Combine history, ML and\nphysical consistency','Layers');
 connect(s,a,b,C.blue,'right','left','elbow');connect(s,a,c,C.teal,'right','left','elbow');
 connect(s,b,d,C.teal,'right','left','elbow');connect(s,c,d,C.teal,'right','left','elbow');
 const outcomes=[['Weather','Keep genuine extremes visible','CloudSun',C.teal],['Fault','Investigate sensor or data issue','Wrench',C.blue],['Uncertain','Request human review','UserRoundSearch',C.amber]];
 outcomes.forEach(([t,b,ic,col],i)=>{let y=204+i*148;let z=shape(s,1002,y,234,108,'none',col);icon(s,ic,1016,y+14,28,col);text(s,t,1055,y+13,165,30,23,true);text(s,b,1017,y+53,204,53,18,false,C.muted);connect(s,d,z,col,'right','left','elbow');});
 text(s,'Original observations stay intact. Operators review proposed corrections separately.',44,643,1180,28,19,false,C.teal);
 note(s,'Source: local T/P/RH contract and pipeline. Virtual Buddy uses eligible nearby peers. Six technical classes group into these outcomes for explanation.');
}
{
 const s=header('TECHNICAL APPROACH',3);
 const inp=block(s,40,199,215,326,'INPUT','Temperature\nPressure\nRelative humidity\nStation ID + timestamp','RadioTower',C.blue);
 const val=block(s,303,222,204,273,'Validation','Time + schema\nHandle data gaps\nSave raw values','ListChecks',C.blue);
 const ml=block(s,555,123,250,217,'Temporal + ML','Causal history features\nIsolation Forest score','BrainCircuit');
 const phy=block(s,555,384,250,217,'Physics + peers','T/P/RH relationships\nTrusted station comparison','Network');
 const fus=block(s,856,230,174,273,'Decision','Combine checks\nExplain cause\nFlag uncertainty','Layers',C.teal);
 const out=block(s,1080,230,160,273,'OUTPUT','Map + reports\nIncidents\nHuman review','MonitorCheck',C.amber);
 connect(s,inp,val,C.blue);connect(s,val,ml,C.blue,'right','left','elbow');connect(s,val,phy,C.teal,'right','left','elbow');connect(s,ml,fus,C.teal,'right','left','elbow');connect(s,phy,fus,C.teal,'right','left','elbow');connect(s,fus,out,C.amber);
 text(s,'Readings',257,321,60,25,12,false,C.blue);text(s,'Evidence',805,334,65,25,12,false,C.teal);
 text(s,'Healthy / Weather / Sensor fault\nData issue / Complex / Needs review',846,541,400,65,19,false,C.muted);
 shape(s,40,621,1200,49,C.paleBlue,'none');
 const names=[['react','React'],['threedotjs','Three.js'],['fastapi','FastAPI'],['python','Python'],['sqlite','SQLite'],['scikitlearn','scikit-learn']];
 for(let i=0;i<names.length;i++){let [f,l]=names[i],x=185+i*172;s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'docs/presentation/pitch/logos',f+'.svg'))),contentType:'image/svg+xml',alt:l,position:{left:x,top:631,width:28,height:28},fit:'contain'});text(s,l,x+36,636,130,28,16,true);}
 text(s,'TECH STACK',55,638,120,24,15,true,C.teal);
 note(s,'Current architecture: React/Three.js UI, FastAPI/Python, scikit-learn Isolation Forest, SQLite. Causal features only. No NWP. Raw values and correction proposals stored separately. Six output classes retained. Evidence strength is uncalibrated. Icons Lucide ISC, logo sources in pitch/logos/SOURCES.md.');
}
{
 const s=header('FEASIBILITY & VIABILITY',4);
 text(s,'Built and working',44,131,520,40,28,true,C.teal);
 const facts=[['Technical','Map, history, detection and review work\ntogether in a local prototype.','Laptop'],['Financial','Open-source tools reduce licensing needs.\nHosting and support costs need a pilot.','Coins'],['Operational','Uses standard temperature, pressure and\nhumidity inputs from weather stations.','RadioTower']];
 facts.forEach(([h,b,ic],i)=>{let y=189+i*108;icon(s,ic,48,y+4,36,C.teal);text(s,h,103,y,430,30,22,true);text(s,b,103,y+36,470,61,20,false,C.muted);});
 text(s,'Fault recall in the synthetic test (%)',44,524,540,30,22,true);
 const chart=s.charts.add('bar',{position:{left:44,top:563,width:520,height:88},categories:['Baseline','SkyGuard'],series:[{name:'Recall',values:[77.47,85.76],fill:C.teal}],barOptions:{direction:'bar',gapWidth:65},hasLegend:false,dataLabels:{showValue:true,position:'outEnd'},xAxis:{minimumScale:0,maximumScale:100},chartFill:C.white,chartLine:{fill:'none',width:0}});applyPresentationChartFont(chart,{fontFamily:FONT});
 text(s,'4,032 simulated observations / 24 unseen stations / 7 scenarios',44,652,560,22,15,false,C.muted);
 const core=shape(s,851,329,179,119,C.paleAmber,C.amber);text(s,'FIELD\nVALIDATION',869,359,145,70,24,true,C.ink,'center');
 const nodes=[{x:643,y:167,t:'Real observations',b:'Connect an authorised\nAWS feed.',ic:'PlugZap',side:'left'},{x:1038,y:167,t:'Expert labels',b:'Label faults and\nweather events.',ic:'UserRoundCheck',side:'right'},{x:643,y:488,t:'New conditions',b:'Test different stations\nand seasons.',ic:'CloudSun',side:'left'},{x:1038,y:488,t:'Measure value',b:'Measure false alerts\nand review time.',ic:'Gauge',side:'right'}];
 nodes.forEach(n=>{let a=shape(s,n.x,n.y,198,143,C.white,C.teal);icon(s,n.ic,n.x+15,n.y+15,26,C.teal);text(s,n.t,n.x+49,n.y+18,140,49,19,true);text(s,n.b,n.x+15,n.y+77,170,60,18,false,C.muted);connect(s,core,a,C.teal,n.y<329?'top':'bottom',n.y<329?'bottom':'top','straight');});
 text(s,'Known limit: weather recall 9.72%. Field accuracy is unproven.',643,649,590,26,16,false,C.muted);
 note(s,'Paired benchmark ml/artifacts/evaluation_v2_comparison.json. 4,032 samples,24 station identities,7 scenarios. Fault recall77.47%/85.76%, weather recall9.72%. Same simulator family, not field validation. Financial and operational benefits require measurement.');
}
{
 const s=header('IMPACT & BENEFITS',5,'A station report turns scattered readings into evidence an operator can review.');
 const pic=new Uint8Array(await fs.readFile(path.join(DIR,'prototype.png')));
 s.images.add({blob:pic,contentType:'image/png',alt:'Actual SkyGuard station map prototype with synthetic data',position:{left:44,top:178,width:601,height:448},fit:'contain'});
 text(s,'ACTUAL PROTOTYPE / SIMULATED STATIONS',65,643,566,26,16,true,C.teal);
 const steps=[['Locate the station','Map status dots identify stations\nthat need attention.','MapPin'],['Understand the alert','History and nearby observations\nhelp explain the likely cause.','ScanSearch'],['Record the decision','Reviews and proposed fixes retain\na traceable record.','ClipboardCheck']];
 let last;steps.forEach(([h,b,ic],i)=>{let y=185+i*143;let a=shape(s,718,y,518,119,'none',C.line);icon(s,ic,735,y+19,36,C.teal);text(s,h,790,y+18,420,31,24,true);text(s,b,790,y+62,425,58,20,false,C.muted);if(last)connect(s,last,a,C.teal,'bottom','top');last=a;});
 text(s,'Expected benefit',718,632,235,26,19,true,C.teal);text(s,'Less searching and more focused investigations.',718,655,520,23,17,false,C.muted);
 note(s,'Screenshot captured from the actual local SkyGuard station UI this turn. Data is simulated. Operator workflow is implemented; time and cost savings not field measured. Regional teams can track recurring incidents. Original observations retained.');
}
// 6. Research references mapped to design choices, with editable links in notes.
{
 const s=header('RESEARCH & REFERENCES',6,'Each source informed a specific part of the project.');
 const rows=[
 ['SIH26073 problem statement','AWS anomaly-detection need and scope','Defines the target users and T/P/RH task.','FileText'],
 ['IMD surface instrumentation','AWS measurements and monitoring','Informs observation metadata and station context.','RadioTower'],
 ['WMO Guide No. 8','Measurement methods and data quality','Guides physical plausibility and quality checks.','BookOpen'],
 ['scikit-learn: Isolation Forest','Unsupervised anomaly detection','Supports the ML score alongside other evidence.','BrainCircuit'],
 ['PMFBY WINDS / OpenStreetMap','Station maps and geographic detail','Inspires zoom behaviour and location exploration.','MapPinned']
 ];
 text(s,'SOURCE',98,172,440,30,18,true,C.blue);text(s,'HOW IT INFORMED SKYGUARD',657,172,560,30,18,true,C.teal);
 rows.forEach(([h,sub,b,ic],i)=>{const y=215+i*78;icon(s,ic,49,y+5,31,C.blue);text(s,h,99,y,478,30,22,true);text(s,sub,99,y+30,478,26,17,false,C.muted);const a=shape(s,590,y+18,2,2,'none','none'),z=shape(s,634,y+18,2,2,'none','none');connect(s,a,z,C.teal);text(s,b,657,y+9,577,50,21,false,C.ink);if(i<4)shape(s,99,y+66,1135,1,C.line,'none','rect');});
 text(s,'Project evidence: reproducible evaluation artifact and recorded limitations accompany the prototype.',44,635,1192,30,18,false,C.teal);
 note(s,'References:\nSIH problem statement supplied by user: references/tprh-revision.txt and original brief.\nIMD: https://mausam.imd.gov.in/imd_latest/contents/surface-met.php\nWMO: https://wmo.int/publication-series/guide-instruments-and-methods-of-observation-wmo-no-8\nscikit-learn: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html\nPMFBY: https://pmfby.gov.in/winds/weather\nOpenStreetMap: https://www.openstreetmap.org\nLocal evidence: ml/artifacts/evaluation_v2_comparison.json and docs/LIMITATIONS.md.\nVisual direction: user-supplied SIH reference screenshots (technical flow and feasibility slide).');
}
await fs.writeFile(path.join(DIR,'deck-v2.json'),JSON.stringify(P.toProto()));
await(await PresentationFile.exportPptx(P)).save(path.join(DIR,'candidate-v2.pptx'));
for(let i=0;i<P.slides.items.length;i++){const s=P.slides.items[i];const png=await P.export({slide:s,format:'png',scale:1.25});await fs.writeFile(path.join(DIR,`v2-slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));}
console.log('Rendered six slides');
const finalPath=path.join(ROOT,'docs/presentation/redesign/output/SkyGuard-SIH-2026-Reference-Final.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:path.join(DIR,'candidate-v2.pptx'),finalPath,pythonExecutable:'/Users/bhavesh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:6,requiredNativeChartOwnerSlides:[4],fontPolicy:{basis:'design',families:[FONT]},materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,receiptPath:path.join(DIR,'validation-reference-final.json')});
console.log(finalPath);
