from fastapi import APIRouter, Depends, Header, HTTPException, status
from schemas.auth import MyPageData
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from schemas.auth import UserCreate, UserInDB, UserUpdate
import crud
from database import get_db
from utils.security import verify_password

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """회원가입 API"""
    existing_user = await crud.get_user_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    
    await crud.create_user(db=db, user=user_in)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=None)

@router.post("/login", response_model=UserInDB)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """로그인 API"""
    user = await crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "responseData": None,
                "statusCode": status.HTTP_401_UNAUTHORIZED,
                "message": "아이디 또는 비밀번호가 잘못되었습니다.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserInDB.from_orm(user)

@router.get("/me", response_model=MyPageData)
async def get_me(
    user_id: int = Header(..., alias="user-id"),
    db: AsyncSession = Depends(get_db)
):
    """마이페이지 정보 조회 API"""
    mypage_data = await crud.get_user_responses(db, user_id=user_id)
    if not mypage_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return mypage_data

@router.put("/me", response_model=UserInDB)
async def update_me(
    user_in: "UserUpdate",
    user_id: int = Header(..., alias="user-id"),
    db: AsyncSession = Depends(get_db)
):
    """사용자 정보 수정 API"""
    updated_user = await crud.update_user(db, user_id=user_id, user_in=user_in)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if isinstance(updated_user, str):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=updated_user)
    return updated_user