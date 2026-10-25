import test from 'node:test';
import assert from 'node:assert/strict';
import {startLiveUpdates} from '../public/live-data.js';
import {matchesProfile} from '../public/preferences.js';
import {briefMatches} from '../public/briefing-core.js';
import {filterSignals} from '../public/core.js';
import {evidenceHtml} from '../public/evidence-ui.js';
test('live polling preserves newest data, pauses hidden tabs and retries after errors',async()=>{
 let callback,hidden=false,requests=0,fail=false;const seen=[],events=[];const doc={get hidden(){return hidden;},addEventListener(){},removeEventListener(){}};
 const control=startLiveUpdates({initial:{generatedAt:'2026-10-25T01:00:00Z'},documentRef:doc,schedule:fn=>{callback=fn;return 1;},cancel:()=>{},load:async()=>{requests++;if(fail)throw Error('offline');return {generatedAt:'2026-10-25T02:00:00Z'};},onData:d=>seen.push(d.generatedAt),onError:()=>events.push('retry')});
 await control.check();assert.equal(seen.length,1);await control.check();assert.equal(seen.length,1);hidden=true;await control.check();assert.equal(requests,2);hidden=false;fail=true;await control.check();assert.deepEqual(events,['retry']);assert.equal(typeof callback,'function');control.stop();await control.check();assert.equal(requests,3);
});
test('secondary services match consistently across board, preferences and briefings; aliases are hidden',()=>{
 const now=Date.now(),s={id:'a',title:'Water and PFAS',agency:'County',jurisdiction:'MD',category:'Water',serviceTags:['Water','PFAS'],status:'open-solicitation',verification:'verified',verifiedAt:new Date(now).toISOString(),deadline:new Date(now+86400000).toISOString()};const alias={...s,id:'alias',duplicateOf:'a'};
 assert.equal(matchesProfile(s,{regions:['MD'],services:['PFAS']}),true);assert.equal(matchesProfile(alias,{regions:[],services:[]}),false);assert.equal(filterSignals([s,alias],{category:'PFAS',query:'Maryland PFAS'}).length,1);assert.equal(briefMatches([s,alias],{regions:['MD'],services:['PFAS']}).length,1);
});
test('document excerpts and source labels are escaped in detail rendering',()=>{
 const html=evidenceHtml({documentReview:'Partial extraction',documentAnalysis:[{title:'<script>evil()</script>',url:'javascript:alert(1)',status:'extracted',pagesRead:2,pageCount:4,checkedAt:new Date().toISOString(),excerpts:{scope:[{page:1,text:'<img src=x onerror=alert(1)>'}]}}]});assert.ok(!html.includes('<script>'));assert.ok(html.includes('&lt;img'));assert.ok(html.includes('href="#"'));assert.ok(html.includes('PDF page 1'));
});
