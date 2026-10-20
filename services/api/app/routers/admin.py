"""All administrative reads and writes require the same native capability and MFA."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.platform import Account
from ..identity.dependencies import require_admin
from ..admin_schemas import (
    RoleChange, PlantWrite, StationWrite, AdminAccountView, AdminPlantView,
    AdminStationView, AdminHistoryEvent, AdminStatus,
)
from ..http.contracts import Page
from ..services import admin

router=APIRouter(prefix='/admin',tags=['administration'])


@router.get('/users', response_model=Page[AdminAccountView])
def users(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),q:str=Query('',max_length=200),
          db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.users(db,offset,limit,q)


@router.patch('/users/{account_id}', response_model=AdminAccountView)
def roles(account_id:str,body:RoleChange,db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.change_roles(db,actor,account_id,body)


@router.get('/plants', response_model=Page[AdminPlantView])
def plants(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.plants(db,offset,limit)


@router.post('/plants', status_code=201, response_model=AdminPlantView)
def create_plant(body:PlantWrite,db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.save_plant(db,actor,body)


@router.put('/plants/{plant_id}', response_model=AdminPlantView)
def update_plant(plant_id:int,body:PlantWrite,db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.save_plant(db,actor,body,plant_id)


@router.get('/stations', response_model=Page[AdminStationView])
def stations(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.stations(db,offset,limit)


@router.post('/stations', status_code=201, response_model=AdminStationView)
def create_station(body:StationWrite,db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.save_station(db,actor,body)


@router.put('/stations/{code}', response_model=AdminStationView)
def update_station(code:str,body:StationWrite,db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.save_station(db,actor,body,code)


@router.get('/history', response_model=Page[AdminHistoryEvent])
def history(offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),actor:Account=Depends(require_admin)):
    return admin.history(db,offset,limit)


@router.get('/status', response_model=AdminStatus)
def status(actor:Account=Depends(require_admin)):
    return admin.status()
