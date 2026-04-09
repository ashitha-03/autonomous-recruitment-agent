import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

# ✅ Required for get_current_user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ✅ Credentials loaded from .env via pydantic settings
def _build_users_db():
    email = settings.hr_email.strip().lower()
    return {
        email: {
            "email": email,
            "name": "HR Manager",
            "role": "hr",
            "password": settings.hr_password.strip(),
            "company": "10xDS",
        }
    }

USERS_DB = _build_users_db()


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_email: str
    user_role: str


class UserOut(BaseModel):
    email: str
    name: str
    role: str


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in USERS_DB:
            raise credentials_exception
        return USERS_DB[email]
    except JWTError:
        raise credentials_exception


@router.post("/login", response_model=Token)
async def login(data: LoginRequest):
    username = data.email.strip().lower()
    password = data.password.strip()

    user = USERS_DB.get(username)

    if not user or password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": user["email"], "role": user["role"]})

    return Token(
        access_token=token,
        token_type="bearer",
        user_name=user["name"],
        user_email=user["email"],
        user_role=user["role"],
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)