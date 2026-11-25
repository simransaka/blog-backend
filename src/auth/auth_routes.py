from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db, User

from .auth_schema import (
    SignupRequest,
    UserResponse,
    TokenResponse,
    LoginRequest
)

from .auth_utils import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# signup
@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db)
):
    email = payload.email.lower()

    # check if email already exists
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # hash password
    hashed_password = hash_password(payload.password)

    # create new user
    new_user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    return new_user



# login
@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    # find user by email
    user = db.query(User).filter(
        User.email == payload.email.lower()
    ).first()

    # verify credentials
    if not user or not verify_password(
        payload.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # generate jwt token
    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }