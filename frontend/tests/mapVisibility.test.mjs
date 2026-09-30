import {test} from 'node:test';
import assert from 'node:assert/strict';
import {visibleStationIds} from '../src/mapVisibility.ts';

test('zoom separates nearby real locations without moving markers',()=>{
 const points=[{id:'selected',x:50,y:50},{id:'nearby',x:70,y:50},{id:'distant',x:120,y:50}];
 assert.deepEqual(visibleStationIds(points,300,200),['selected','distant']);
 assert.deepEqual(visibleStationIds(points.map(p=>({...p,x:p.x*2,y:p.y*2})),600,400),['selected','nearby','distant']);
});
test('pan reveals previously offscreen stations and preserves priority',()=>{
 const points=[{id:'selected',x:50,y:50},{id:'overlap',x:51,y:50},{id:'outside',x:310,y:50}];
 assert.deepEqual(visibleStationIds(points,300,200),['selected']);
 assert.deepEqual(visibleStationIds(points.map(p=>({...p,x:p.x-100})),300,200),['outside']);
});
