from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Sensor(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, null=False)
    n = fields.IntField(default=10)

    def __str__(self):
        return self.name


class Data(Model):
    id = fields.IntField(pk=True)
    sensor_id = fields.IntField(null=False)
    value = fields.DecimalField(null=False, max_digits=8, decimal_places=2)

    def __str__(self):
        return self.value


Sensor_Pydantic = pydantic_model_creator(Sensor, name="Sensor")
SensorIn_Pydantic = pydantic_model_creator(Sensor, name="SensorIn", exclude_readonly=True)
Data_Pydantic = pydantic_model_creator(Data, name="Data")
DataIn_Pydantic = pydantic_model_creator(Data, name="DataIn", exclude_readonly=True)
