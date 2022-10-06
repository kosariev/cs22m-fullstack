from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Review(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=True, default="(Not given)")
    description = fields.TextField(null=True, default="(Not given)")

    def __str__(self):
        return self.name


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=64, null=False)
    fullname = fields.CharField(max_length=255, null=False)
    email = fields.CharField(max_length=255, null=False)
    hashed_password = fields.CharField(max_length=255, null=False)
    disabled = fields.BooleanField(default=False)

    def __str__(self):
        return self.username


User_Pydantic = pydantic_model_creator(User, name="User")
Review_Pydantic = pydantic_model_creator(Review, name="Review")
ReviewIn_Pydantic = pydantic_model_creator(Review, name="ReviewIn", exclude_readonly=True)
