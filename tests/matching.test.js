import test from 'node:test';import assert from 'node:assert/strict';
import {normalizeProfile,profileFit,matchesProfile} from '../public/preferences.js';
import {briefMatches,renderBriefing} from '../public/briefing-core.js';
import {sourceFreshness} from '../public/source-freshness.js';
import {evidenceHtml} from '../public/evidence-ui.js';
const at=Date.parse('2026-10-25T20:00:00Z');
const bid={id:'bid',title:'Remediation',jurisdiction:'MD',category:'Cleanup',serviceTags:['Cleanup','Testing'],status:'open-solicitation',verification:'verified',verifiedAt:new Date(at).toISOString(),deadline:new Date(at+86400000).toISOString(),sourceUrl:'https://county.gov/bid'};
test('contract capacity uses only contract values and retains missing budgets and grant amounts',()=>{
 const profile={regions:['MD'],services:['Testing'],maxContractValue:100000};
 assert.equal(matchesProfile({...bid,amount:2000000},profile),true);
 assert.equal(matchesProfile({...bid,contractValue:200000},profile),false);
 assert.equal(matchesProfile({...bid,status:'funding-signal',amount:2000000,contractValue:2000000},profile),true);
 assert.ok(profileFit(bid,profile).review.some(x=>x.includes('not verified')));
 assert.equal(matchesProfile({...bid,contractValue:50000},profile),true);
});
test('self-reported designations and mandatory meetings cause review rather than qualification claims',()=>{
 const record={...bid,requiredBusinessCertifications:[{id:'MBE'}],prebidAttendance:'mandatory'};
 const fit=profileFit(record,{certifications:['MBE']});assert.ok(fit.reasons.some(x=>x.includes('You report MBE')));assert.ok(fit.review.some(x=>x.includes('attendance')));
 const missing=profileFit(record,{});assert.equal(missing.matches,true);assert.ok(missing.review.some(x=>x.includes('not recorded')));
});
test('invalid and old profiles normalize without inventing capacity or certifications',()=>{
 assert.deepEqual(normalizeProfile({regions:['XX'],services:['unknown'],certifications:['fake'],minContractValue:-5,maxContractValue:'NaN'}),{regions:[],services:[]});
 assert.equal(normalizeProfile({minContractValue:200,maxContractValue:100}).maxContractValue,undefined);
});
test('dashboard and digest share capacity matching and explain unresolved qualification checks',()=>{
 const profile={regions:['MD'],services:['Testing'],maxContractValue:100000};
 const rows=[bid,{...bid,id:'large',contractValue:200000}];assert.deepEqual(briefMatches(rows,profile,at).map(s=>s.id),['bid']);
 const out=renderBriefing({signals:[{...bid,qualificationChecklist:[{title:'Bonding and insurance',state:'needs-review'}]}],datasetAt:bid.verifiedAt,profile,at});
 assert.ok(out.text.includes('Bonding and insurance'));assert.ok(out.html.includes('Contract value is not verified'));
});
test('freshness follows each source schedule and rejects future or absent evidence times',()=>{
 assert.equal(sourceFreshness({id:'sam',status:'verified',lastChecked:new Date(at-24*3600000).toISOString()},at).fresh,true);
 assert.equal(sourceFreshness({id:'county',status:'checked',lastChecked:new Date(at-4*3600000).toISOString()},at).fresh,false);
 assert.equal(sourceFreshness({status:'checked'},at).fresh,false);
});
test('checklist escapes source excerpts and unsafe URLs',()=>{
 const html=evidenceHtml({qualificationChecklist:[{title:'Bonds',state:'evidence-found',evidence:[{text:'<script>bad</script>',url:'javascript:alert(1)',page:2}]}]});
 assert.ok(!html.includes('<script>'));assert.ok(!html.includes('javascript:'));assert.ok(html.includes('PDF page 2'));
});

test('fit sorting keeps a matching bid with unknown budget above an out-of-region bid',()=>{
 const profile={regions:['MD'],services:['Cleanup'],maxContractValue:100000};
 assert.ok(profileFit(bid,profile).rank>profileFit({...bid,jurisdiction:'VA',contractValue:50000},profile).rank);
});
