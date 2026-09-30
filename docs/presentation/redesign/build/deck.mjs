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
const C={ink:'#17324D',muted:'#52667B',blue:'#2868B2',teal:'#168B83',amber:'#D69A24',paleBlue:'#EEF5FD',paleTeal:'#EDF8F5',paleAmber:'#FFF7E6',line:'#CDDBE8',white:'#FFFFFF'};
const sih=new Uint8Array(await fs.readFile(path.join(DIR,'sih.png')));
function shape(s,x,y,w,h,fill=C.white,stroke=C.line,geometry='roundRect'){return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:1.6},borderRadius:12});}
function text(s,t,x,y,w,h=50,size=22,bold=false,color=C.ink,align='left') {const a=shape(s,x,y,w,h,'none','none','textbox');a.text=t;a.text.style={typeface:FONT,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',autoFit:'none',insets:{top:0,left:0,right:0,bottom:0}};return a;}
function icon(s,name,x,y,size=34,color=C.blue){const svg=renderToStaticMarkup(React.createElement(icons[name],{size:64,color,strokeWidth:1.8}));return s.images.add({blob:new TextEncoder().encode(svg),contentType:'image/svg+xml',alt:name,position:{left:x,top:y,width:size,height:size},fit:'contain'});}
function connect(s,a,b,color=C.blue,from='right',to='left',kind='straight'){return s.shapes.connect(a,b,{fromSide:from,toSide:to,kind,line:{fill:color,width:2.2},tail:{type:'triangle',width:'sm',length:'sm'}});}
function box(s,x,y,w,h,title,body,color=C.blue,fill=C.paleBlue,ico){const a=shape(s,x,y,w,h,fill,color);if(ico)icon(s,ico,x+18,y+18,30,color);text(s,title,x+(ico?60:20),y+19,w-(ico?78:40),48,w<220?20:22,true);if(body)text(s,body,x+20,y+62,w-40,h-66,w<280?18:20,false,C.muted);return a;}
function header(title,n,subtitle){const s=P.slides.add();s.background.fill=C.white;text(s,'OFF BY ONE',44,27,190,27,18,true,C.blue);text(s,title,250,22,730,52,34,true);s.images.add({blob:sih,contentType:'image/png',alt:'Smart India Hackathon 2026',fit:'contain',position:{left:1085,top:15,width:150,height:72}});shape(s,44,94,1192,2,C.line,'none','rect');if(subtitle)text(s,subtitle,44,112,1185,42,22,false,C.muted);shape(s,0,682,1280,38,C.blue,'none','rect');text(s,'SKYGUARD  /  SIH26073',44,693,700,20,14,true,C.white);text(s,String(n).padStart(2,'0'),1185,690,50,24,18,true,C.white,'right');return s;}
function note(s,t){s.speakerNotes.textFrame.setText(t);}
// 1. A simple cover with a compact visual explanation of the project.
{
 const s=header('SKYGUARD',1);
 text(s,'Weather station data\nwith an explanation',55,157,610,122,46,true);
 text(s,'AI/ML-Based Intelligent Anomaly Detection\nfor Automatic Weather Stations (AWS)',57,303,590,80,26,false,C.muted);
 text(s,'Problem statement 26073',57,428,560,35,23,true,C.blue);
 text(s,'Disaster Management  •  Software\nTeam OFF BY ONE  •  ID 132195',57,478,580,72,22,false,C.muted);
 text(s,'Working prototype with 500 simulated stations',57,588,580,35,20,false,C.teal);
 const a=box(s,738,161,435,125,'AWS observations','Temperature  •  Pressure  •  Humidity',C.blue,C.paleBlue,'RadioTower');
 const b=box(s,738,342,435,128,'SkyGuard checks','History, ML, physics and nearby stations',C.teal,C.paleTeal,'ScanSearch');connect(s,a,b,C.blue,'bottom','top');
 const c=box(s,738,526,435,111,'Evidence for the operator','Likely cause and a clear review action',C.amber,C.paleAmber,'ClipboardCheck');connect(s,b,c,C.teal,'bottom','top');
 note(s,'Project scope: references/tprh-revision.txt; README.md. Demo network contains synthetic observations. No real IMD/AWS feed is connected. Team details carried from user presentation.');
}
// 2. Proposed solution: observation → parallel checks → decision → response.
{
 const s=header('PROPOSED SOLUTION',2,'A sudden change may be weather, a sensor fault or a data-delivery problem.');
 const input=box(s,44,275,228,170,'Reading','A sudden change\nneeds a cause.',C.blue,C.paleBlue,'Thermometer');
 const hist=box(s,327,187,250,150,'Station history','Check jumps, drift\nand stuck values.',C.blue,C.paleBlue,'History');
 const context=box(s,327,394,250,164,'Virtual Buddy','Check related readings\nand trusted neighbours.',C.teal,C.paleTeal,'Network');
 const merge=box(s,636,279,244,177,'Combine clues','Explain the likely cause\nand missing evidence.',C.teal,C.paleTeal,'Layers');
 connect(s,input,hist,C.blue,'right','left','elbow');connect(s,input,context,C.teal,'right','left','elbow');connect(s,hist,merge,C.blue,'right','left','elbow');connect(s,context,merge,C.teal,'right','left','elbow');
 const out1=box(s,943,173,293,128,'Weather supported','Keep the event visible.',C.teal,C.paleTeal,'CloudSun');
 const out2=box(s,943,337,293,128,'Fault supported','Open a sensor or data incident.',C.blue,C.paleBlue,'Wrench');
 const out3=box(s,943,501,293,128,'Evidence uncertain','Ask an operator to review.',C.amber,C.paleAmber,'UserRoundSearch');
 connect(s,merge,out1,C.teal,'right','left','elbow');connect(s,merge,out2,C.blue);connect(s,merge,out3,C.amber,'right','left','elbow');
 icon(s,'ShieldCheck',44,608,27,C.teal);text(s,'Original readings remain intact; approved correction proposals are stored separately.',85,608,820,45,20,false,C.muted);
 note(s,'Source: local pipeline implementation, README.md and docs/LIMITATIONS.md. This slide groups operational outcomes for explanation; the implementation retains six classes, shown on technical slide. Nearby-station evidence is conditional on sufficient trusted peers.');
}
// 3. Technical approach: native editable boxes and connected arrows.
{
 const s=header('TECHNICAL APPROACH',3,'Each observation passes through validation, parallel checks and an explained decision.');
 const inp=box(s,44,286,198,179,'Input','T / P / RH\nStation ID + time\nHTTP or CSV',C.blue,C.paleBlue,'RadioTower');
 const valid=box(s,282,286,206,179,'Validate','Time + schema\nLate / missing data\nSave originals',C.blue,C.paleBlue,'ListChecks');
 const model=box(s,532,178,267,162,'History + ML','Past-only features\nSpikes, drift, flatlines\nIsolation Forest score',C.blue,C.paleBlue,'BrainCircuit');
 const phys=box(s,532,401,267,162,'Physics + peers','T/P/RH consistency\nNearby trusted stations\nAvailable context only',C.teal,C.paleTeal,'Network');
 const fuse=box(s,851,282,179,180,'Fuse','Weigh clues\nClassify cause\nGive reasons',C.teal,C.paleTeal,'Layers');
 const report=box(s,1072,282,164,180,'Review','History\nIncidents\nReview actions',C.amber,C.paleAmber,'MonitorCheck');
 connect(s,inp,valid);connect(s,valid,model,C.blue,'right','left','elbow');connect(s,valid,phys,C.teal,'right','left','elbow');connect(s,model,fuse,C.blue,'right','left','elbow');connect(s,phys,fuse,C.teal,'right','left','elbow');connect(s,fuse,report,C.amber);
 text(s,'OUTPUTS',851,485,370,27,17,true,C.blue);text(s,'Healthy · Weather · Sensor fault\nData issue · Complex · Needs review',851,518,378,67,19,false,C.muted);
 const db=shape(s,44,586,755,52,C.paleBlue,C.line);icon(s,'Database',61,598,28,C.blue);text(s,'SQLite: raw observations, decisions, review history and correction proposals',101,600,680,28,18,false,C.ink);
 const names=[['react','React'],['threedotjs','Three.js'],['fastapi','FastAPI'],['python','Python'],['sqlite','SQLite'],['scikitlearn','scikit-learn']];
 for(let i=0;i<names.length;i++){const [file,label]=names[i],x=170+i*172;const bytes=await fs.readFile(path.join(ROOT,'docs/presentation/pitch/logos',file+'.svg'));s.images.add({blob:new Uint8Array(bytes),contentType:'image/svg+xml',alt:label+' logo',fit:'contain',position:{left:x,top:646,width:24,height:24}});text(s,label,x+32,650,127,24,16,true,C.muted);}
 text(s,'STACK',44,650,90,24,16,true,C.blue);
 note(s,'Architecture reflects backend/API, storage and frontend in README.md. All online features use current and past data. Isolation Forest trains on synthetic normal data. Evidence strength is uncalibrated. No NWP or external forecasts are implemented. Technology logo SVGs: docs/presentation/pitch/logos/SOURCES.md. Icons: lucide-react, ISC license.');
}
// 4. Reference-inspired feasibility chain with explicit risks and responses.
{
 const s=header('FEASIBILITY & VIABILITY',4,'A working software prototype with a defined path to field validation.');
 const a=box(s,44,171,547,130,'Technical feasibility','Integrated map, reports and anomaly checks;\n500 simulated stations with historical observations.',C.blue,C.paleBlue,'Laptop');
 const b=box(s,44,321,547,130,'Operational viability','Open-source stack and existing T/P/RH inputs.\nDeployment and support costs need pilot measurement.',C.teal,C.paleTeal,'Settings2');connect(s,a,b,C.teal,'bottom','top');
 text(s,'FAULT RECALL (%) · PAIRED SYNTHETIC TEST',44,473,560,32,20,true,C.blue);
 const chart=s.charts.add('bar',{position:{left:44,top:510,width:540,height:116},categories:['Baseline','SkyGuard'],series:[{name:'Fault recall',values:[77.47,85.76],fill:C.blue}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:80},hasLegend:false,dataLabels:{showValue:true,position:'outEnd'},xAxis:{minimumScale:0,maximumScale:100},chartFill:C.white,chartLine:{fill:'none',width:0}});applyPresentationChartFont(chart,{fontFamily:FONT});
 text(s,'4,032 observations · 24 unseen station identities · 7 scenarios',44,637,605,27,16,false,C.muted);
 text(s,'CHALLENGE',660,167,245,30,18,true,C.blue);text(s,'RESPONSE',975,167,255,30,18,true,C.teal);
 const risks=[['Limited real data','Connect real AWS data.\nLabel events with experts.','PlugZap'],['Weather recall: 9.72%','Expand weather cases.\nKeep human review.','CloudSun'],['Untested field performance','Test new seasons/sites.\nMeasure errors and cost.','Gauge']];
 risks.forEach(([r,t,ic],i)=>{const y=219+i*143;const l=box(s,660,y,245,111,r,'',C.amber,C.paleAmber,ic);const rr=shape(s,966,y,270,111,C.paleTeal,C.teal);text(s,t,984,y+30,234,72,18,false,C.ink);connect(s,l,rr,C.teal);});
 text(s,'The benchmark uses simulated data. Field accuracy remains unproven.',660,647,575,26,16,false,C.muted);
 note(s,'Measured values from ml/artifacts/evaluation_v2_comparison.json: 4,032 observations, 24 unseen station identities, 7 scenarios; fault recall 77.47% vs 85.76%; weather recall 9.72%. Same simulator family; not independent field validation. API and UI capabilities from README.md. No operating-cost or hardware-speed claims are made.');
}
// 5. Benefits through a concrete operator journey and stakeholder outcomes.
{
 const s=header('IMPACT & BENEFITS',5,'The operator can follow an alert through to a recorded action.');
 const steps=[['Locate','Select a flagged station\non the India map.','MapPin'],['Understand','Read its history, peer\ncomparison and explanation.','ChartNoAxesCombined'],['Decide','Review the incident or\npropose a correction.','UserRoundCheck'],['Trace','Retain original readings\nand the decision history.','FileClock']];let last;
 steps.forEach(([t,b,ic],i)=>{const n=box(s,44+i*305,182,277,185,t,b,i<2?C.blue:C.teal,i<2?C.paleBlue:C.paleTeal,ic);if(last)connect(s,last,n,i<2?C.blue:C.teal);last=n;});
 text(s,'EXPECTED BENEFITS',44,422,1160,36,22,true,C.blue);
 const groups=[['Station operators','Less searching across screens;\nmore focused sensor investigations.','Wrench'],['Weather-data teams','Consistent evidence and quality flags\nfor reviewing suspect observations.','ListChecks'],['Regional teams','Station health and incident counts\nto identify recurring local issues.','MapPinned']];
 groups.forEach(([h,b,ic],i)=>{const x=44+i*405;icon(s,ic,x,478,35,C.teal);text(s,h,x+49,477,330,35,23,true);text(s,b,x,528,380,70,21,false,C.muted);});
 shape(s,44,623,1192,38,C.paleAmber,'none');text(s,'Pilot measures: operator review time, missed faults, false alerts and maintenance follow-through.',61,632,1160,26,18,false,C.ink);
 note(s,'Operational workflow is implemented in local UI/API per README.md and WORK_LOG.md. Benefits are expected outcomes to measure in a pilot, not quantified field savings. Maintenance scheduling and personnel management are not claimed as implemented.');
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
await fs.writeFile(path.join(DIR,'deck.json'),JSON.stringify(P.toProto()));
await(await PresentationFile.exportPptx(P)).save(path.join(DIR,'candidate.pptx'));
for(let i=0;i<P.slides.items.length;i++){const s=P.slides.items[i];const png=await P.export({slide:s,format:'png',scale:1.25});await fs.writeFile(path.join(DIR,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));}
console.log('Rendered six slides');
const finalPath=path.join(ROOT,'docs/presentation/redesign/output/SkyGuard-SIH-2026.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:path.join(DIR,'candidate.pptx'),finalPath,pythonExecutable:'/Users/bhavesh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:6,requiredNativeChartOwnerSlides:[4],fontPolicy:{basis:'design',families:[FONT]},materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,receiptPath:path.join(DIR,'validation.json')});
console.log(finalPath);
