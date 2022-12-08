from fastapi import FastAPI, HTTPException
from fastapi_pagination import LimitOffsetPage, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from exam_models import Sensor, Sensor_Pydantic, SensorIn_Pydantic, Data, Data_Pydantic, DataIn_Pydantic


tags_metadata = [{
    "name": "Application",
    "description": "Default endpoint",
}]

app = FastAPI(
    title="Exam",
    description="API for Sensors",
    version="CS-22m/Fullstack",
    contact={
        "name": "Oleksandr Kosariev",
        "email": "oleksandr.kosariev@gmail.com",
    },
    openapi_tags=tags_metadata,
)

sensor_pydantic = pydantic_model_creator(Sensor)
data_pydantic = pydantic_model_creator(Data)


class Status(BaseModel):
    message: str


@app.get("/", tags=["Application"])
async def entrypoint():
    """
    Display's welcome message
    """
    return {"message": "Hello World"}


@app.post("/create/", response_model=Sensor_Pydantic, tags=["Sensor"])
async def create_new_sensor(sensor: SensorIn_Pydantic):
    """
    Create a new sensor
    """
    sensor_obj = await Sensor.create(**sensor.dict(exclude_unset=True))
    return await Sensor_Pydantic.from_tortoise_orm(sensor_obj)


@app.get("/sensors/", response_model=LimitOffsetPage[Sensor_Pydantic], tags=["Sensor"])
async def fetch_all_sensors():
    """
    Return all available sensors
    """
    return await paginate(Sensor)


@app.get("/sensor/{sensor_id}", response_model=Sensor_Pydantic, responses={404: {"model": HTTPNotFoundError}}, tags=["Sensor"])
async def get_sensor_by_id(sensor_id: int):
    """
    Get a sensor by id
    """
    return await Sensor_Pydantic.from_queryset_single(Sensor.get(id=sensor_id))


@app.get("/data/{sensor_id}",  responses={404: {"model": HTTPNotFoundError}}, tags=["Data"])
async def get_sensor_data(sensor_id: int):
    """
    Get data by sensor id
    """
    sensor = await Sensor.filter(id=sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    sensor_obj = await Sensor_Pydantic.from_queryset_single(Sensor.get(id=sensor_id))
    return await Data.filter(sensor_id=sensor_id).limit(sensor_obj.n).order_by('-id')


@app.put("/sensor/{sensor_id}", response_model=Sensor_Pydantic, responses={404: {"model": HTTPNotFoundError}}, tags=["Sensor"])
async def update_sensor(sensor_id: int, sensor: SensorIn_Pydantic):
    await Sensor.filter(id=sensor_id).update(**sensor.dict(exclude_unset=True))
    return await Sensor_Pydantic.from_queryset_single(Sensor.get(id=sensor_id))


@app.post("/add/", response_model=Data_Pydantic, tags=["Data"])
async def add_data_to_sensor(data: DataIn_Pydantic):
    """
    Add data to sensor
    """
    sensor = await Sensor.filter(id=data.sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor {data.sensor_id} not found")
    sensor_obj = await Sensor_Pydantic.from_queryset_single(Sensor.get(id=data.sensor_id))
    data_ids = await Data.filter(sensor_id=sensor_obj.id).limit(sensor_obj.n).order_by('-id')
    last_data_id = None
    for data_id in data_ids:
        last_data_id = data_id.id
    if last_data_id:
        await Data.filter(id__lte=last_data_id).delete()
    data_obj = await Data.create(**data.dict(exclude_unset=True))
    return await Data_Pydantic.from_tortoise_orm(data_obj)


@app.delete("/sensor/{sensor_id}", response_model=Status, responses={404: {"model": HTTPNotFoundError}}, tags=["Sensor"])
async def delete_sensor(sensor_id: int):
    """
    Delete existing sensor by id
    """
    sensor_deleted = await Sensor.filter(id=sensor_id).delete()
    if not sensor_deleted:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")
    await Data.filter(sensor_id=sensor_id).delete()
    return Status(message=f"Deleted sensor {sensor_id}")


register_tortoise(
    app,
    db_url="sqlite://exam.db",
    modules={"models": ["exam_models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

add_pagination(app)
