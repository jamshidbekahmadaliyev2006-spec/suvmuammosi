from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Role


class LoginIn(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    role: Role


class SessionOut(BaseModel):
    user: UserOut
    csrf_token: str


class ProfileUpdateIn(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    current_password: str | None = Field(default=None, min_length=1, max_length=256)
    new_password: str | None = Field(default=None, min_length=8, max_length=256)

