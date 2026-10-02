from io import BytesIO
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.platform import Account
from app.identity.dependencies import require_account
from app.reporting import storage

class MemoryStore:
    def __init__(self):self.values={}
    def put_object(self,**args):self.values[args['Key']]=args['Body']
    def get_object(self,**args):return {'Body':BytesIO(self.values[args['Key']])}
    def delete_object(self,**args):self.values.pop(args['Key'],None)


def test_real_image_validation_and_scoped_download(monkeypatch):
    with SessionLocal() as db:
        users=[Account(issuer='https://fixture.invalid',subject=str(uuid4()),email='test@example.com') for _ in range(2)]
        db.add_all(users);db.commit()
        for user in users:db.refresh(user)
    monkeypatch.setattr(storage,'client',lambda:MemoryStore())
    store=MemoryStore();monkeypatch.setattr(storage,'client',lambda:store)
    app.dependency_overrides[require_account]=lambda:users[0]
    try:
        client=TestClient(app)
        assert client.post('/api/v1/media',files={'file':('bad.jpg',b'<script>bad</script>')}).status_code==422
        stream=BytesIO();Image.new('RGB',(8,8),'white').save(stream,format='JPEG')
        response=client.post('/api/v1/media',files={'file':('photo.jpg',stream.getvalue())})
        assert response.status_code==201
        media_id=response.json()['id']
        own=client.get('/api/v1/media/'+media_id)
        assert own.status_code==200 and own.content==stream.getvalue()
        assert own.headers['cache-control']=='no-store'
        app.dependency_overrides[require_account]=lambda:users[1]
        assert client.get('/api/v1/media/'+media_id).status_code==404
    finally:app.dependency_overrides.clear()
