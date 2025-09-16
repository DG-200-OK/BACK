from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import models
from schemas.auth import UserCreate, UserUpdate
from schemas.survey import SurveyCreate
from schemas.response import ResponseCreate
from utils.security import get_password_hash

# ====================
#       User
# ====================
async def get_user_by_username(db: AsyncSession, username: str):
    """username으로 사용자를 조회합니다."""
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    """새로운 사용자를 생성합니다."""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_in: "UserUpdate"):
    user_result = await db.execute(select(models.User).where(models.User.userId == user_id))
    user = user_result.scalars().first()
    if not user:
        return None

    if user_in.username:
        existing_user = await get_user_by_username(db, username=user_in.username)
        if existing_user and existing_user.userId != user_id:
            return "Username already registered"
        user.username = user_in.username

    if user_in.password:
        user.password = get_password_hash(user_in.password)

    await db.commit()
    await db.refresh(user)
    return user

# ====================
#       Survey
# ====================
async def create_survey(db: AsyncSession, survey: SurveyCreate) -> None:
    """새로운 설문을 생성하고 연관된 캡션들도 함께 생성합니다."""
    db_survey = models.Survey(
        imageUrl=survey.imageUrl,
        country=survey.country,
        category=survey.category,
        title=survey.title,
        userId=survey.userId
    )
    db.add(db_survey)
    await db.flush()  # survey의 survey_id를 얻기 위해 flush

    levels = {"level1": survey.level1, "level2": survey.level2, "level3": survey.level3, "level4": survey.level4}
    for level, text in levels.items():
        if text and text.strip():
            db_caption = models.Caption(
                surveyId=db_survey.surveyId,
                text=text,
                type=level
            )
            db.add(db_caption)
    
    await db.commit()

async def get_surveys_with_progress(db: AsyncSession, user_id: int):
    """사용자의 진행 상황을 포함하여 전체 설문 목록을 조회합니다."""
    # 모든 설문과 관련 캡션을 가져옵니다.
    surveys_result = await db.execute(
        select(models.Survey)
        .options(selectinload(models.Survey.captions))
    )
    surveys = surveys_result.scalars().all()

    # 각 설문에 대한 진행 상황을 계산합니다.
    for survey in surveys:
        total_captions = len(survey.captions)
        if total_captions == 0:
            survey.progress = 0.0
            continue

        # 사용자가 이 설문에 대해 제출한 응답 수를 계산합니다.
        response_count_result = await db.execute(
            select(func.count(models.Response.responseId))
            .join(models.Caption)
            .where(
                models.Response.userId == user_id,
                models.Caption.surveyId == survey.surveyId
            )
        )
        response_count = response_count_result.scalar_one()

        survey.progress = (response_count / total_captions) if total_captions > 0 else 0.0

    return surveys

async def get_survey(db: AsyncSession, survey_id: int):
    """ID로 특정 설문을 조회합니다. 캡션도 함께 로드합니다."""
    result = await db.execute(
        select(models.Survey).options(selectinload(models.Survey.captions)).filter(models.Survey.surveyId == survey_id)
    )
    survey = result.scalars().first()
    if survey:
        # Explicitly touch the relationship to ensure it's loaded
        # before the session might be closed or the async context lost.
        _ = survey.captions
    return survey

async def get_surveys_by_user_id(db: AsyncSession, user_id: int):
    """user_id로 사용자가 등록한 설문을 조회합니다."""
    result = await db.execute(
        select(models.Survey)
        .where(models.Survey.userId == user_id)
    )
    surveys = result.scalars().all()
    return surveys

# ====================
#      Response
# ====================
async def create_response(db: AsyncSession, response: ResponseCreate):
    """설문에 대한 응답을 생성합니다."""
    response_data = response.model_dump()
    response_data['time'] = response_data.pop('responseTime', 0.0)
    db_response = models.Response(**response_data)
    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)
    return db_response

async def get_user_responses(db: AsyncSession, user_id: int):
    # Get user
    user_result = await db.execute(select(models.User).where(models.User.userId == user_id))
    user = user_result.scalars().first()
    if not user:
        return None

    # Get surveys the user has responded to
    surveys_result = await db.execute(
        select(models.Survey)
        .join(models.Caption, models.Survey.surveyId == models.Caption.surveyId)
        .join(models.Response, models.Caption.captionId == models.Response.captionId)
        .where(models.Response.userId == user_id)
        .distinct()
    )
    surveys = surveys_result.scalars().all()

    participated_surveys = [
        {
            "title": survey.title,
            "category": survey.category,
            "country": survey.country,
            "imageUrl": survey.imageUrl,
        }
        for survey in surveys
    ]

    return {
        "username": user.username,
        "participatedSurvey": participated_surveys,
    }