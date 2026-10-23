import {escapeHtml as e} from './core.js';
import {regions,services,normalizeProfile,profileDescription} from './preferences.js';
const $=s=>document.querySelector(s);
const key='cleanupsignal.profile';
let profile={regions:[],services:[]},inquiryRegions=[];
try{profile=normalizeProfile(JSON.parse(localStorage.getItem(key)));}catch{}
export function currentProfile(){return profile;}
export function inquiryScope(){return inquiryRegions.length?`Requested research jurisdictions: ${inquiryRegions.join(', ')}. Saved project profile: ${profileDescription(profile)}`:`Saved project profile: ${profileDescription(profile)}`;}
function updateInquiry(){$('#inquiryScope').textContent=inquiryScope();}
function fillProfile(){for(const el of $('#profileForm').querySelectorAll('input[type=checkbox]'))el.checked=profile[el.name].includes(el.value);}
export function renderCategories(signals){
 const tile=([id,title,description])=>{const count=signals.filter(s=>s.category===id).length;return `<article class="category-card"><span class="category-symbol" aria-hidden="true">${id==='Assessment'?'◎':id==='Cleanup'?'↗':id==='Multipurpose'?'▦':'+'}</span><span class="tag ${count?'open':''}">${count?`${count} PUBLISHED SIGNAL${count===1?'':'S'}`:'COVERAGE NOT YET ACTIVE'}</span><h3>${e(title)}</h3><p>${e(description)}</p>${count?`<a href="#dashboard" data-category="${e(id)}">Browse ${count} signals ↗</a>`:`<a href="#profile" data-interest="${e(id)}">Add research interest ↗</a>`}</article>`;};
 $('#homeCategories').innerHTML=services.slice(0,3).map(tile).join('');$('#categoryDirectory').innerHTML=services.map(tile).join('');$('#homeTotal').textContent=signals.length;
}
export function initContractor({applyCategory,profileChanged}){
 $('#profileRegions').innerHTML=regions.map(([id,name])=>`<label><input type="checkbox" name="regions" value="${id}"> ${name}</label>`).join('');
 $('#profileServices').innerHTML=services.map(([id,title])=>`<label><input type="checkbox" name="services" value="${id}"> ${title}</label>`).join('');fillProfile();updateInquiry();
 $('#profileForm').addEventListener('submit',ev=>{ev.preventDefault();const f=new FormData(ev.currentTarget);const next=normalizeProfile({regions:f.getAll('regions'),services:f.getAll('services')});try{localStorage.setItem(key,JSON.stringify(next));profile=next;$('#profileResult').textContent='Saved on this browser. '+profileDescription(profile)+'. No email alerts have been enabled.';}catch{profile=next;$('#profileResult').textContent='Browser storage is unavailable. Preferences apply for this visit only.';}updateInquiry();profileChanged();});
 $('#clearProfile').addEventListener('click',()=>{profile={regions:[],services:[]};try{localStorage.removeItem(key);}catch{}fillProfile();updateInquiry();$('#profileResult').textContent='Profile cleared. All published services and jurisdictions are included.';profileChanged();});
 $('#useProfile').addEventListener('click',()=>{$('#matchProfile').checked=true;profileChanged();});
 document.addEventListener('click',ev=>{const category=ev.target.closest('[data-category]');if(category)applyCategory(category.dataset.category);const interest=ev.target.closest('[data-interest]');if(interest){const box=$('#profileServices').querySelector(`input[value="${interest.dataset.interest}"]`);if(box)box.checked=true;$('#profileResult').textContent='Research interest selected. Save your profile below to keep it on this browser.';}const example=ev.target.closest('[data-example]');if(example){$('#matchProfile').checked=false;$('#search').value='Annapolis';$('#jurisdiction').value='';$('#category').value='';$('#status').value='';profileChanged();}});
 function quote(){const selected=[...$('#quoteRegions').querySelectorAll('input:checked')].map(el=>el.value);$('#quoteSummary').textContent=selected.length?`Requested: ${selected.join(' + ')} · Proposed pilot: $99/month per firm. Scope subject to agreement.`:'Select at least one jurisdiction to prepare an inquiry.';$('#useQuote').disabled=!selected.length;return selected;}
 $('#quoteRegions').addEventListener('change',quote);quote();$('#useQuote').addEventListener('click',()=>{inquiryRegions=quote();updateInquiry();location.hash='pilot';});
}
