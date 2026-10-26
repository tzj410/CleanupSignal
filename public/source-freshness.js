// Per-source evidence age, separate from the time a new dataset was published.
export function sourceFreshness(source,at=Date.now()){
 const interval=source.intervalHours||(source.id==='sam'?24:1),limit=(2*interval+1)*3600000;
 const checked=source.lastSuccess||(['verified','checked'].includes(source.status)?source.lastChecked:null);
 const age=at-Date.parse(checked),fresh=Number.isFinite(age)&&age>=-300000&&age<=limit;
 return {checked,fresh,interval,overdueHours:limit/3600000};
}
