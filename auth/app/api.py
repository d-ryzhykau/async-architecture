from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import UUID4, BaseModel, ConfigDict, EmailStr, constr

from .db import Session
from .models import Role
from .security import create_access_token, decode_access_token
from .services import UserEmailAlreadyUsed, UserNotFound, UserService

app = FastAPI()


def get_db_session():
    """Dependency that provides DB session."""
    with Session() as session:
        yield session


def get_user_service(
    session: Annotated[Session, Depends(get_db_session)],
):
    return UserService(session)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Dependency that provides access token data."""
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


class RolesRequired:
    """Dependency that checks if the role in the access token matches."""

    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: Annotated[dict, Depends(get_token_data)]):
        if token_data.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@app.post("/token", response_model=TokenResponse)
def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    user = user_service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    return {
        "access_token": create_access_token(
            {
                "sub": str(user.uuid),
                "email": user.email,
                "role": user.role.value,
            },
        ),
        "token_type": "bearer",
    }


class UserDataResponse(BaseModel):
    uuid: UUID4
    email: EmailStr
    role: Role

    model_config = ConfigDict(from_attributes=True)


@app.get(
    "/users/me",
    response_model=UserDataResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No data for current User.",
        },
    },
)
def get_self(
    token_data: Annotated[dict, Depends(get_token_data)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user = user_service.get_user_by_uuid(uuid=token_data["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    return user


@app.get(
    "/users/",
    dependencies=[Depends(RolesRequired("manager"))],
    response_model=List[UserDataResponse],
)
def get_users(user_service: Annotated[UserService, Depends(get_user_service)]):
    return user_service.get_users()


class CreateUserRequest(BaseModel):
    email: EmailStr
    role: Role
    password: str = constr(min_length=8, max_length=256)


@app.post(
    "/users/",
    dependencies=[Depends(RolesRequired("manager"))],
    status_code=status.HTTP_201_CREATED,
    response_model=UserDataResponse,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Email is already used",
        },
    },
)
def create_user(
    payload: CreateUserRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user = user_service.create_user(
            email=payload.email,
            role=payload.role,
            password=payload.password,
        )
    except UserEmailAlreadyUsed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already used",
        )

    return user


class UpdateUserRequest(BaseModel):
    email: EmailStr


@app.patch(
    "/users/{uuid}",
    dependencies=[Depends(RolesRequired("manager"))],
    response_model=UserDataResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "User with given UUID was not found",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Email is already used",
        },
    },
)
def update_user(
    uuid: UUID4,
    payload: UpdateUserRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user = user_service.update_user(
            uuid=uuid,
            new_email=payload.email,
        )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    except UserEmailAlreadyUsed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already used",
        )

    return user


@app.delete(
    "/users/{uuid}",
    dependencies=[Depends(RolesRequired("manager"))],
    status_code=204,
    response_class=Response,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "User with given UUID was not found",
        },
    },
)
def delete_user(
    uuid: UUID4,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user = user_service.delete_user(uuid)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    return user
