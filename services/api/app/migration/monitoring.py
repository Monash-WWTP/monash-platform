"""Transactional real monitoring snapshot import, preserving source payload/provenance."""
import csv
import hashlib
import json
from pathlib import Path
from sqlalchemy.orm import Session
from ..db.platform import Station, Sample, ImportRecord

NUMERIC={'bod','cod','nh3n','no3n','ph','oil_grease','tss','temperature','latitude','longitude'}
INTEGER={'id','sampling','source_year'}
FLAGS={'bod_bdl','cod_bdl','nh3n_bdl','no3n_bdl','ph_bdl','oil_grease_bdl','tss_bdl'}


def rows(path: Path, columns: list[str]):
    with path.open(newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=columns:
            raise ValueError('Source columns do not match declared snapshot')
        result=[]
        for row in reader:
            converted={}
            for key,value in row.items():
                if value=='': converted[key]=None
                elif key in FLAGS:
                    if value not in {'True','False'}:raise ValueError('Invalid censoring flag')
                    converted[key]=value=='True'
                elif key in NUMERIC:converted[key]=float(value)
                elif key in INTEGER:converted[key]=int(value)
                else:converted[key]=value
            result.append(converted)
        return result


def import_snapshot(db:Session, directory:Path)->dict:
    manifest=json.loads((directory/'manifest.json').read_text())
    source_id=manifest['dataset']+':'+manifest['version']
    payload=b''.join((directory/name).read_bytes() for name in
                     ['manifest.json','stations.csv','effluent_samples.csv','emission_factors.csv'])
    digest=hashlib.sha256(payload).hexdigest()
    prior=db.get(ImportRecord,source_id)
    if prior:
        if prior.digest!=digest:raise ValueError('Source changed for an already imported version')
        return prior.manifest['reconciliation']
    stations=rows(directory/'stations.csv',manifest['tables']['stations']['columns'])
    samples=rows(directory/'effluent_samples.csv',manifest['tables']['effluent_samples']['columns'])
    factors=rows(directory/'emission_factors.csv',manifest['tables']['emission_factors']['columns'])
    for name,data in [('stations',stations),('effluent_samples',samples),('emission_factors',factors)]:
        if len(data)!=manifest['tables'][name]['rows']:raise ValueError('Declared row count mismatch')
    if len({r['code'] for r in stations})!=len(stations) or len({r['id'] for r in samples})!=len(samples):
        raise ValueError('Duplicate source identifiers')
    if any(row['station_code'] not in {s['code'] for s in stations} for row in samples):
        raise ValueError('Sample refers to unknown station')
    for row in stations:
        if db.get(Station,row['code']):raise ValueError('Station identifier already belongs to another import')
        db.add(Station(code=row['code'],payload=row))
    db.flush()
    for row in samples:
        if db.get(Sample,row['id']):raise ValueError('Sample identifier already belongs to another import')
        db.add(Sample(id=row['id'],station_code=row['station_code'],payload=row))
    counts={'stations':len(stations),'effluent_samples':len(samples),'emission_factors':len(factors)}
    db.add(ImportRecord(source_id=source_id,digest=digest,
                       manifest={**manifest,'emission_factor_reference':factors,'reconciliation':counts}))
    db.commit()
    return counts
