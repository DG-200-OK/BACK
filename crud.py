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
async def create_survey(db: AsyncSession, survey: SurveyCreate) -> models.Survey:
    """새로운 설문을 생성하고 연관된 캡션들도 함께 생성합니다."""
    db_survey = models.Survey(
        image_url=survey.imageUrl,
        country=survey.country,
        category=survey.category,
        title=survey.title
    )
    db.add(db_survey)
    await db.flush()  # survey의 survey_id를 얻기 위해 flush

    for caption_data in survey.captions:
        db_caption = models.Caption(
            surveyId=db_survey.surveyId,
            text=caption_data.text,
            type=caption_data.type
        )
        db.add(db_caption)
    
    await db.commit()
    await db.refresh(db_survey)
    return db_survey

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
    return result.scalars().first()

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

    # Get user responses
    responses_result = await db.execute(
        select(models.Response)
        .options(selectinload(models.Response.caption).selectinload(models.Caption.survey))
        .where(models.Response.userId == user_id)
    )
    responses = responses_result.scalars().all()

    # Format responses
    formatted_responses = []
    for res in responses:
        formatted_responses.append({
            "surveyId": res.caption.survey.surveyId,
            "choice": res.captionId
        })

    return {
        "username": user.username,
        "responses": formatted_responses
    }