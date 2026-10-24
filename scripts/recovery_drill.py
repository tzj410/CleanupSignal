#!/usr/bin/env python3
"""Restore an existing private SQL export and compare a synthetic full-data round trip.
Never connects to production or writes dumps under public/. Run before customer enrollment.
"""
import argparse,datetime as dt,hashlib,json,pathlib,sqlite3,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def snapshot(db):
 tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name")]
 result={}
 for table in tables:
  rows=[list(r) for r in db.execute('SELECT * FROM "'+table+'"')]
  rows.sort(key=lambda x:json.dumps(x,default=str,sort_keys=True));result[table]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows,default=str,sort_keys=True).encode()).hexdigest()}
 return result

def restore(sql):
 db=sqlite3.connect(':memory:');db.executescript(sql);problems=db.execute('PRAGMA foreign_key_check').fetchall()
 if problems:raise ValueError('Restored export has foreign-key failures')
 return db

def drill():
 started=time.monotonic();db=sqlite3.connect(':memory:')
 for file in sorted((ROOT/'migrations').glob('*.sql')):db.executescript(file.read_text())
 db.execute("INSERT INTO companies(id,name,owner_id,plan,subscription_status,period_end) VALUES('drill-co','Recovery fixture','drill-owner','team','active',unixepoch()+86400)")
 db.execute("INSERT INTO members(user_id,company_id,email,role) VALUES('drill-owner','drill-co','owner@example.com','owner')")
 db.execute("INSERT INTO members(user_id,company_id,email,role) VALUES('drill-member','drill-co','member@example.com','member')")
 db.execute("INSERT INTO preferences(company_id,regions,services) VALUES('drill-co','[\"MD\"]','[\"Water\"]')")
 db.execute("INSERT INTO watchlist(company_id,signal_id,note) VALUES('drill-co','fixture-bid','Private synthetic note')")
 db.execute("INSERT INTO support_requests(id,category,email,message) VALUES('CS-recovery-fixture','General question','owner@example.com','Synthetic recovery request')")
 db.execute("INSERT INTO alert_settings(user_id) VALUES('drill-owner')")
 db.execute("INSERT INTO deliveries(id,user_id,kind,payload) VALUES('drill-email','drill-owner','digest','{}')")
 db.commit();before=snapshot(db);sql='\n'.join(db.iterdump());restored=restore(sql)
 assert snapshot(restored)==before,'Full-data checksums differ after restore'
 assert restored.execute("SELECT m.user_id FROM members m JOIN companies c ON c.id=m.company_id WHERE c.id='drill-co' ORDER BY m.user_id").fetchall()==[('drill-member',),('drill-owner',)]
 # Capacity triggers must survive restoration too.
 restored.execute("INSERT INTO members(user_id,company_id,email,role) VALUES('third','drill-co','third@example.com','member')")
 try:restored.execute("INSERT INTO members(user_id,company_id,email,role) VALUES('fourth','drill-co','fourth@example.com','member')")
 except sqlite3.IntegrityError as e:assert 'seat_limit' in str(e)
 else:raise AssertionError('Restored seat enforcement is missing')
 report={'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'kind':'synthetic-full-data-roundtrip','tables':len(before),'rows':sum(t['rows'] for t in before.values()),'checksumsMatch':True,'foreignKeysValid':True,'seatEnforcementValid':True,'elapsedSeconds':round(time.monotonic()-started,3),'productionModified':False}
 db.close();restored.close();return report

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--private-export',type=pathlib.Path);args=parser.parse_args();report=drill()
 if args.private_export:
  db=restore(args.private_export.read_text());report['privateExportRestored']={'tables':len(snapshot(db)),'rows':sum(t['rows'] for t in snapshot(db).values()),'foreignKeysValid':True};db.close()
 print(json.dumps(report,indent=2))
