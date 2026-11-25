from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

import jwt

from src.database import get_db, User
from .auth_config import SECRET_KEY, ALGORITHM


# extract bearer token from incoming requests
oauth2 = HTTPBearer()



def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2),
    db: Session = Depends(get_db)
) -> User:
    
    credentials_exceptiion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        token = credentials.credentials
        
        # decode and verify jwt token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # extract user ID
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exceptiion

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exceptiion

    # find user in DB
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_exceptiion

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return user