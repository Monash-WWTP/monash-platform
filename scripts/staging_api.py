"""Run local API/migrations/import with restricted staging credentials, never prints secrets."""
import argparse,json,os,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['migrate','import','serve','identity','build'])
a=p.parse_args()
secret_file=ROOT/'infra/staging/.env.local'
if secret_file.stat().st_mode & 0o077:raise ValueError('Staging custody permissions are unsafe')
values=dict(line.split('=',1) for line in secret_file.read_text().splitlines() if line and not line.startswith('#'))
env={**os.environ,'DATABASE_URL':'postgresql+psycopg://monash:'+values['APP_DB_PASSWORD']+'@127.0.0.1:5544/monash',
    'APP_ENV':'staging','AUTH_MODE':'oidc','OIDC_ISSUER':'http://localhost:9100/',
    'OIDC_DISCOVERY_URL':'http://localhost:9100/application/o/monash-web/.well-known/openid-configuration',
    'OIDC_JWKS_URL':'http://localhost:9100/application/o/monash-web/jwks/',
    'OIDC_CLIENT_ID':'monash-web','OIDC_MOBILE_CLIENT_ID':'citizen-mobile',
    'OIDC_CLIENT_SECRET':values.get('MONASH_WEB_SECRET',''),'WEB_ORIGIN':'http://localhost:8180',
    'OIDC_CALLBACK_URL':'http://localhost:8180/api/v1/auth/callback','SESSION_SECURE':'false',
    'CORS_ORIGINS':'http://localhost:8180','STORAGE_ENDPOINT':'http://127.0.0.1:3900',
    'STORAGE_ACCESS_KEY':values['STORAGE_ACCESS_KEY'],'STORAGE_SECRET_KEY':values['STORAGE_SECRET_KEY']}
commands={
 'migrate':['uv','run','--locked','alembic','-c','services/api/alembic.ini','upgrade','head'],
 'import':['uv','run','--locked','python','scripts/migrate_platform.py','--public-snapshot',str(ROOT/'data/public')],
 'serve':['uv','run','--locked','uvicorn','app.main:app','--reload','--host','127.0.0.1','--port','8181'],
 'build':['docker','build','-f','services/api/Dockerfile','-t','monash-api:local','.']}
if a.action=='identity':
    source='import os\nos.environ["MONASH_WEB_SECRET"]='+repr(values['MONASH_WEB_SECRET'])+'\n'+(ROOT/'infra/staging/identity/bootstrap.py').read_text()
    log=ROOT/'.superpowers/sdd/2026-10-03-local-shared-backend/identity-bootstrap.log'
    with log.open('w') as stream:
        result=subprocess.run(['docker','exec','-i','monash-staging-identity-server-1','python'],input=source,
                              text=True,stdout=stream,stderr=stream)
    print('Identity configuration exit:',result.returncode)
    raise SystemExit(result.returncode)
subprocess.run(commands[a.action],cwd=ROOT,env=env,check=True)
