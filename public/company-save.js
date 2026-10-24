export async function saveToCompany(signalId){
 let response=await fetch('/api/watchlist',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({signalId})});
 if(response.status===401){const refresh=await fetch('/api/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(refresh.ok)response=await fetch('/api/watchlist',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({signalId})});}
 let data;try{data=await response.json();}catch{throw new Error('Company accounts are being prepared. Your browser watchlist is available.');}
 if(response.status===401||response.status===404){location.assign('/account.html');return 'Open your company workspace to continue.';}
 if(!response.ok)throw new Error(data.error||'Could not save to your company.');return 'Saved to company workspace. Existing team notes were preserved.';
}
