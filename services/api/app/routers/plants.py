from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..http.errors import ApiError
from ..db.models import Plant
from ..db.session import get_db
from ..schemas import PlantDetailOut, PlantOut

router = APIRouter(prefix="/plants", tags=["plants"])


@router.get("", response_model=list[PlantOut])
def list_plants(db: Session = Depends(get_db)):
    return db.query(Plant).order_by(Plant.id).all()


@router.get("/{plant_id}", response_model=PlantDetailOut)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.get(Plant, plant_id)
    if not plant:
        raise ApiError(404, "plant_not_found", "Plant not found")
    return plant
