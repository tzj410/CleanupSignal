import test from 'node:test';
import assert from 'node:assert/strict';
import {effectiveStatus,filterSignals,makeCsv,escapeHtml,safeUrl} from '../public/core.js';
const at=Date.parse('2026-10-23T18:00:00Z');
const records=[{id:'a',title:'Annapolis cleanup',agency:'City',jurisdiction:'MD',category:'Cleanup',status:'funding-signal',amount:4000000,announcedAt:'2026-06-24'},{id:'b',title:'Virginia assessment',jurisdiction:'VA',category:'Assessment',status:'open-solicitation',deadline:'2026-10-22T18:00:00Z',verification:'verified',announcedAt:'2026-10-01'}];
test('expired and unverified bids cannot display as open',()=>{assert.equal(effectiveStatus(records[1],at),'closed');assert.equal(effectiveStatus({...records[1],deadline:'2027-01-01T00:00:00Z',verification:'stale'},at),'unconfirmed');});
test('combined filters find only matching public signals',()=>{assert.deepEqual(filterSignals(records,{query:'annapolis',jurisdiction:'MD',category:'Cleanup'},at).map(s=>s.id),['a']);assert.equal(filterSignals(records,{status:'open-solicitation'},at).length,0);assert.equal(filterSignals(records,{jurisdiction:'DC'},at).length,0);});
test('CSV defuses spreadsheet formulas and reports effective status',()=>{const csv=makeCsv([{...records[1],title:'=HYPERLINK("bad")'}],at);assert.ok(csv.includes("'=HYPERLINK"));assert.ok(csv.includes('"closed"'));assert.ok(!csv.includes('"open-solicitation"'));});
test('untrusted source text and URLs are safely rendered',()=>{assert.equal(escapeHtml('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');assert.equal(safeUrl('javascript:alert(1)'),'#');assert.equal(safeUrl('https://epa.gov.attacker.example/'),'#');assert.equal(safeUrl('https://www.epa.gov/test'),'https://www.epa.gov/test');});

import {normalizeProfile,matchesProfile} from '../public/preferences.js';
test('profile combines jurisdictions and services and rejects unknown selections',()=>{
 const profile=normalizeProfile({regions:['MD','XX'],services:['Cleanup','Injected']});
 assert.deepEqual(profile,{regions:['MD'],services:['Cleanup']});
 assert.equal(matchesProfile(records[0],profile),true);
 assert.equal(matchesProfile(records[1],profile),false);
 assert.equal(matchesProfile(records[0],{regions:[],services:['PFAS']}),false);
 assert.equal(matchesProfile(records[0],normalizeProfile(null)),true);
});

import {readFileSync} from 'node:fs';
test('founding plan prices and recipient limits remain consistent in public HTML and JS',()=>{
 const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
 const contractor=readFileSync(new URL('../public/contractor.js',import.meta.url),'utf8');
 const app=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
 for(const [id,monthly,yearly,seats] of [['starter',19,190,1],['team',29,290,3],['business',49,490,8]]){
  assert.ok(html.includes('data-plan-tier="'+id+'" data-monthly="'+monthly+'" data-yearly="'+yearly+'"'));
  assert.ok(contractor.includes(id+':{title:'));
  assert.ok(contractor.includes('monthly:'+monthly+',yearly:'+yearly+',seats:'+seats));
  assert.equal(monthly*10,yearly);
 }
 assert.ok(html.includes('id="pilotBilling"')&&html.includes('id="pilotTeamSize"'));
 assert.ok(app.includes('selectedPricing()'));
 assert.ok(![html,contractor,app].some(text=>text.includes('$99')));
 assert.ok(html.includes('No paid account system, checkout, automatic alerts, or annual billing is active'));
});
