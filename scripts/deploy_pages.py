#!/usr/bin/env python3
"""Repeatable Pages direct uploads, including the API Worker. Never prints credentials."""
import argparse,base64,hashlib,json,mimetypes,os,pathlib,sys,time
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='https://api.cloudflare.com/client/v4'
def api(path,token,body=None,content_type='application/json'):
 raw=(json.dumps(body).encode() if not isinstance(body,bytes) else body) if body is not None else None
 try:
  with urlopen(Request(BASE+path,data=raw,headers={'Authorization':'Bearer '+token,'Content-Type':content_type},method='POST' if raw is not None else 'GET'),timeout=90) as response:result=json.load(response)
 except HTTPError as error:raise RuntimeError('Cloudflare upload failed: HTTP '+str(error.code)) from None
 except (URLError,TimeoutError):raise RuntimeError('Cloudflare upload network failure') from None
 if not result.get('success'):raise RuntimeError('Cloudflare rejected the upload')
 return result.get('result')
def deploy(branch):
 account=os.environ.get('CLOUDFLARE_ACCOUNT_ID');token=os.environ.get('CLOUDFLARE_API_TOKEN')
 if not account or not token:raise RuntimeError('Set Cloudflare account ID and a scoped Pages deployment token')
 prefix=f'/accounts/{account}/pages/projects/cleanupsignal';upload_token=api(prefix+'/upload-token',token)['jwt']
 manifest={};assets={}
 for file in sorted((ROOT/'public').rglob('*')):
  if not file.is_file() or file.name.startswith('_'):continue
  raw=file.read_bytes();key=hashlib.md5(raw).hexdigest();manifest['/'+file.relative_to(ROOT/'public').as_posix()]=key
  assets[key]={'key':key,'value':base64.b64encode(raw).decode(),'base64':True,'metadata':{'contentType':mimetypes.guess_type(str(file))[0] or 'application/octet-stream'}}
 missing=api('/pages/assets/check-missing',upload_token,{'hashes':list(assets)})
 # Small site; split to keep request size bounded as it grows.
 for i in range(0,len(missing),20):api('/pages/assets/upload',upload_token,[assets[k] for k in missing[i:i+20]])
 boundary='CleanupSignal'+hashlib.sha256(os.urandom(32)).hexdigest()[:20];parts=[]
 for name,value in {'branch':branch,'commit_hash':os.environ.get('GITHUB_SHA',''),'commit_message':'Deploy verified CleanupSignal build','manifest':json.dumps(manifest)}.items():
  parts.extend(['--'+boundary,f'Content-Disposition: form-data; name="{name}"','',value])
 for name,ctype in [('_worker.js','application/javascript+module'),('_routes.json','application/json'),('_headers','text/plain')]:
  parts.extend(['--'+boundary,f'Content-Disposition: form-data; name="{name}"; filename="{name}"','Content-Type: '+ctype,'',(ROOT/'public'/name).read_text()])
 parts.extend(['--'+boundary+'--','']);result=api(prefix+'/deployments',token,'\r\n'.join(parts).encode(),'multipart/form-data; boundary='+boundary)
 print('Deployment created:',result['id']);print('URL:',result['url'])
 for attempt in range(24):
  status=api(prefix+'/deployments/'+result['id'],token);stage=status.get('latest_stage',{})
  if stage.get('name')=='deploy' and stage.get('status')=='success':
   print('Production deployment verified successful.');return
  if stage.get('status') in ['failure','canceled']:raise RuntimeError('Deployment failed; inspect the Cloudflare build log before retrying')
  time.sleep(5)
 raise RuntimeError('Deployment verification timed out; inspect Cloudflare before declaring success')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--branch',default='main');args=parser.parse_args()
 try:deploy(args.branch)
 except RuntimeError as error:print(str(error),file=sys.stderr);sys.exit(1)
