from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_pagination import LimitOffsetPage, add_pagination
from fastapi_pagination.ext.tortoise import paginate
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from models import Review, Review_Pydantic, ReviewIn_Pydantic, User, User_Pydantic
import base64
import tortoise.exceptions

tags_metadata = [{
    "name": "Application",
    "description": "Default endpoint",
}]

app = FastAPI(
    title="Library",
    description="Description of library module",
    version="CS-22m/Fullstack",
    contact={
        "name": "Oleksandr Kosariev",
        "email": "oleksandr.kosariev@gmail.com",
    },
    openapi_tags=tags_metadata,
)

review_pydantic = pydantic_model_creator(Review)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str):
    return base64.b64encode(password.encode('ascii')).decode('ascii')


class UserInDB(User):
    hashed_password: str


class Status(BaseModel):
    message: str


class UserInfo(BaseModel):
    username: str


async def get_user(hashed_password: str):
    res = await User_Pydantic.from_queryset_single(User.get(hashed_password=hashed_password))
    return res


async def decode_token(token):
    user = await get_user(token)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await decode_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    #  if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", tags=["Authentication"])
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get token, based on username/password combination
    """
    user_dict = await User_Pydantic.from_queryset_single(User.get(username=form_data.username))

    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    hashed_password = hash_password(form_data.password)
    if not hashed_password == user_dict.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user_dict.hashed_password, "token_type": "bearer"}


@app.get("/users/me", response_model=UserInfo, tags=["User"])
async def return_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Display current logged-in user information
    """
    return current_user


@app.get("/", tags=["Application"])
async def entrypoint():
    """
    Display's welcome message
    """
    return {"message": "Hello World"}


@app.get("/init/", tags=["User"])
async def create_user():
    """
    Create an example user (demo/demo)
    """

    try:
        obj = await User.get(username="demo")
    except tortoise.exceptions.DoesNotExist:
        await User(
            username="demo",
            fullname="Demo User",
            email="demo@demo.local",
            hashed_password=base64.b64encode("demo".encode('ascii')).decode('ascii'),
            disabled=False
        ).save()
    return {"status": "ok"}


@app.get("/reviews/", response_model=LimitOffsetPage[Review_Pydantic], tags=["Review"])
async def fetch_all_reviews():
    """
    Return all available reviews
    """
    return await paginate(Review)


@app.get("/review/{review_id}", response_model=Review_Pydantic, responses={404: {"model": HTTPNotFoundError}},
         tags=["Review"])
async def get_a_single_review_by_id(review_id: int):
    """
    Get a single review by id
    """
    return await Review_Pydantic.from_queryset_single(Review.get(id=review_id))


@app.post("/add/", response_model=Review_Pydantic, tags=["Review"])
async def create_a_new_review(review: ReviewIn_Pydantic):
    """
    Create a new review
    """
    review_obj = await Review.create(**review.dict(exclude_unset=True))
    return await Review_Pydantic.from_tortoise_orm(review_obj)


@app.delete("/delete/{review_id}", response_model=Status, responses={404: {"model": HTTPNotFoundError}}, tags=["Review"])
async def delete_review(review_id: int):
    """
    Delete existing review by id
    """
    deleted_review = await Review.filter(id=review_id).delete()
    if not deleted_review:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    return Status(message=f"Deleted review {review_id}")


register_tortoise(
    app,
    db_url="sqlite://library.db",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

add_pagination(app)
