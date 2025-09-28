import math
import random
from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import models
from schemas.auth import UserCreate, UserUpdate
from schemas.survey import SurveyCreate
from schemas.response import ResponseCreate
from utils.security import get_password_hash
from scipy.stats import wasserstein_distance
import numpy as np

# ====================
#       User
# ====================
async def get_user_by_username(db: AsyncSession, username: str):
    """username으로 사용자를 조회합니다."""
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    """email으로 사용자를 조회합니다."""
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    """새로운 사용자를 생성합니다."""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        password=hashed_password,
        gender=user.gender,
        email=user.email
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate):
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

async def get_surveys_with_progress(db: AsyncSession, user_id: int, category: str | None = None, search: str | None = None):
    """사용자의 진행 상황과 전체 응답 수를 포함하여 전체 설문 목록을 조회합니다."""
    # 1. Get all surveys with their captions
    stmt = select(models.Survey).options(selectinload(models.Survey.captions))
    if category:
        stmt = stmt.filter(models.Survey.category == category)
    if search:
        stmt = stmt.filter(models.Survey.title.ilike(f"%{search}%"))
    surveys_result = await db.execute(stmt)
    surveys = surveys_result.scalars().unique().all()
    survey_map = {s.surveyId: s for s in surveys}

    # Initialize progress and total_responses
    for survey in surveys:
        survey.progress = 0.0
        survey.total_responses = 0

    if not survey_map:
        return []

    # 2. Get all response counts grouped by survey
    response_counts_result = await db.execute(
        select(
            models.Caption.surveyId,
            func.count(models.Response.responseId).label("total_count"),
            func.sum(case((models.Response.userId == user_id, 1), else_=0)).label("user_count")
        )
        .join(models.Response, models.Caption.captionId == models.Response.captionId)
        .where(models.Caption.surveyId.in_(survey_map.keys()))
        .group_by(models.Caption.surveyId)
    )
    response_counts = response_counts_result.all()

    # 3. Assign counts and calculate progress
    for survey_id, total_count, user_count in response_counts:
        if survey_id in survey_map:
            survey = survey_map[survey_id]
            survey.total_responses = total_count
            total_captions = len(survey.captions)
            if total_captions > 0:
                survey.progress = (user_count / total_captions)

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
import httpx

async def create_response(db: AsyncSession, response: ResponseCreate):
    """설문에 대한 응답을 생성합니다."""
    response_data = response.model_dump()
    response_data['time'] = response_data.pop('responseTime', 0.0)
    db_response = models.Response(**response_data)
    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)

    # Count responses for this caption
    response_count_result = await db.execute(
        select(func.count(models.Response.responseId))
        .where(models.Response.captionId == db_response.captionId)
    )
    current_response_count = response_count_result.scalar_one()

    # Count total responses across all captions
    total_response_count_result = await db.execute(
        select(func.count(models.Response.responseId))
    )
    total_response_count = total_response_count_result.scalar_one()

    # Send API request if total response count is multiple of 10
    should_send_request = (total_response_count % 10 == 0)

    if should_send_request:
        try:
            async with httpx.AsyncClient() as client:
                # The request body should contain necessary info for evaluation
                # For now, let's send the captionId
                await client.post(
                    "https://publicly-flying-crane.ngrok-free.app/api/evaluate-with-flag",
                    json={
                        "startCaptionId": db_response.captionId,
                        "endCaptionId": db_response.captionId,
                        "flag": current_response_count
                        },
                    timeout=5.0 # Set a timeout for the request
                )
        except httpx.RequestError as exc:
            # Log the error but don't block the main response flow
            print(f"Error sending evaluation request: {exc}")
        except Exception as exc:
            print(f"An unexpected error occurred during evaluation request: {exc}")

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
        "email": user.email if user.email else "이메일 등록을 하지 않으셨습니다.",
        "participatedSurvey": participated_surveys,
    }

async def get_chart_data(db: AsyncSession, page: int, page_size: int):
    """
    설문별, 캡션 레벨별 응답 평균을 계산하여 차트 데이터를 조회합니다.
    """
    surveys_query = select(models.Survey).options(
        selectinload(models.Survey.captions).options(
            selectinload(models.Caption.responses),
            selectinload(models.Caption.agent_eval_details) # Changed here
        )
    )
    
    total_surveys_result = await db.execute(select(func.count()).select_from(models.Survey))
    total_surveys = total_surveys_result.scalar_one()
    total_pages = math.ceil(total_surveys / page_size)

    offset = (page - 1) * page_size
    surveys_result = await db.execute(
        surveys_query.offset(offset).limit(page_size)
    )
    surveys = surveys_result.scalars().unique().all()

    all_chart_data = []
    for survey in surveys:
        # Group responses and agent evaluations by caption level
        level_responses = {f'레벨{i}': [] for i in range(1, 5)}
        level_agent_eval_details = {f'레벨{i}': [] for i in range(1, 5)} # Changed here
        for caption in survey.captions:
            if caption.type in level_responses:
                level_responses[caption.type].extend(caption.responses)
                level_agent_eval_details[caption.type].extend(caption.agent_eval_details) # Changed here

        # Calculate averages for people
        people_cultural_avgs = []
        people_visual_avgs = []
        people_hallucination_avgs = []

        for i in range(1, 5):
            level = f'레벨{i}'
            responses = level_responses[level]
            response_count = len(responses)

            if response_count == 0:
                people_cultural_avgs.append(0.0)
                people_visual_avgs.append(0.0)
                people_hallucination_avgs.append(0.0)
            else:
                cultural_total = sum(r.cultural for r in responses)
                visual_total = sum(r.visual for r in responses)
                hallucination_total = sum(r.hallucination for r in responses)

                people_cultural_avgs.append(round(cultural_total / response_count, 2))
                people_visual_avgs.append(round(visual_total / response_count, 2))
                people_hallucination_avgs.append(round(hallucination_total / response_count, 2))

        # Calculate averages for agent (using agent_eval_details)
        agent_cultural_avgs = [0.0] * 5 # Initialize with 0.0
        agent_visual_avgs = [0.0] * 5
        agent_hallucination_avgs = [0.0] * 5

        for i in range(1, 5):
            level = f'레벨{i}'
            eval_details = level_agent_eval_details[level] # Changed here

            for detail in eval_details:
                if 1 <= detail.likert <= 5:
                    if detail.type == 'cultural':
                        agent_cultural_avgs[detail.likert - 1] = detail.value
                    elif detail.type == 'visual':
                        agent_visual_avgs[detail.likert - 1] = detail.value
                    elif detail.type == 'hallucination':
                        agent_hallucination_avgs[detail.likert - 1] = detail.value

        chartdata = {
            "cultural": {"people": people_cultural_avgs, "agent": agent_cultural_avgs},
            "visual": {"people": people_visual_avgs, "agent": agent_visual_avgs},
            "hallucination": {"people": people_hallucination_avgs, "agent": agent_hallucination_avgs}
        }
        
        chart_item = {
            "surveyId": survey.surveyId,
            "title": survey.title,
            "imageUrl": survey.imageUrl,
            "chartdata": chartdata
        }
        all_chart_data.append(chart_item)

    return {"totalPages": total_pages, "chartList": all_chart_data}

# ====================
#       Ranking
# ====================
async def get_user_rankings(db: AsyncSession):
    """사용자별 응답 수를 기준으로 랭킹을 조회합니다."""
    result = await db.execute(
        select(
            models.User.username,
            func.count(models.Response.responseId).label("response_count")
        )
        .join(models.Response, models.User.userId == models.Response.userId)
        .where(models.Response.time > 1.9, models.User.email != None)
        .group_by(models.User.username)
        .order_by(func.count(models.Response.responseId).desc())
    )
    
    rankings = result.all()
    
    # Sort rankings by response_count in descending order
    rankings.sort(key=lambda x: x.response_count, reverse=True)

    ranked_data = []
    current_rank = 0
    last_count = -1
    for i, (username, count) in enumerate(rankings):
        if count != last_count:
            current_rank = i + 1
            last_count = count
        ranked_data.append({
            "username": username,
            "responseCount": count,
            "rank": current_rank
        })

    return ranked_data

async def get_ongoing_surveys(db: AsyncSession, user_id: int):
    """진행 중인 설문 목록을 조회합니다. (progress가 0.25, 0.5, 0.75인 설문)"""
    surveys = await get_surveys_with_progress(db, user_id)
    ongoing_surveys = [survey for survey in surveys if survey.progress in [0.25, 0.5, 0.75]]
    return ongoing_surveys

async def get_all_surveys_for_upload(db: AsyncSession):
    """업로드를 위해 모든 설문 목록을 조회합니다."""
    result = await db.execute(select(models.Survey))
    surveys = result.scalars().all()
    return surveys

async def update_survey_image_url(db: AsyncSession, survey_id: int, new_image_url: str):
    """설문의 이미지 URL을 업데이트합니다."""
    result = await db.execute(select(models.Survey).where(models.Survey.surveyId == survey_id))
    survey = result.scalars().first()
    if survey:
        survey.imageUrl = new_image_url
        await db.commit()
        await db.refresh(survey)
    return survey

async def get_chart_data_by_caption(db: AsyncSession, page: int, page_size: int, category: str | None = None, search: str | None = None, user_id: int | None = None):
    """
    캡션별 응답을 집계하여 차트 데이터를 조회합니다.
    """
    captions_query = select(models.Caption).options(
        selectinload(models.Caption.survey),
        selectinload(models.Caption.responses),
        selectinload(models.Caption.agent_eval_details)
    )

    if user_id:
        captions_query = captions_query.join(models.Survey).filter(models.Survey.userId == user_id)

    captions_result = await db.execute(captions_query)
    all_captions = captions_result.scalars().unique().all()

    if category:
        all_captions = [caption for caption in all_captions if caption.survey.category == category]
    
    if search:
        all_captions = [caption for caption in all_captions if search.lower() in caption.survey.title.lower()]

    random.shuffle(all_captions)

    total_captions = len(all_captions)
    total_pages = math.ceil(total_captions / page_size)

    offset = (page - 1) * page_size
    captions = all_captions[offset:offset + page_size]

    response_data = []
    for caption in captions:
        
        def calculate_distribution(data_list, is_agent=False):
            cultural_scores = [0.0] * 5
            visual_scores = [0.0] * 5
            hallucination_scores = [0.0] * 5
            
            if is_agent:
                for item in data_list:
                    if 1 <= item.likert <= 5:
                        if item.type == 'cultural':
                            cultural_scores[item.likert - 1] = item.value
                        elif item.type == 'visual':
                            visual_scores[item.likert - 1] = item.value
                        elif item.type == 'hallucination':
                            hallucination_scores[item.likert - 1] = item.value
                return (cultural_scores, visual_scores, hallucination_scores)

            else:
                for r in data_list:
                    cultural = int(r.cultural)
                    visual = int(r.visual)
                    hallucination = int(r.hallucination)

                    if 1 <= cultural <= 5:
                        cultural_scores[cultural - 1] += 1
                    if 1 <= visual <= 5:
                        visual_scores[visual - 1] += 1
                    if 1 <= hallucination <= 5:
                        hallucination_scores[hallucination - 1] += 1
                
                total_responses = len(data_list)
                if total_responses == 0:
                    return ([0.0] * 5, [0.0] * 5, [0.0] * 5)

                return (
                    [round((s / total_responses) * 100, 2) for s in cultural_scores],
                    [round((s / total_responses) * 100, 2) for s in visual_scores],
                    [round((s / total_responses) * 100, 2) for s in hallucination_scores]
                )

        people_cultural, people_visual, people_hallucination = calculate_distribution(caption.responses)
        agent_cultural, agent_visual, agent_hallucination = calculate_distribution(caption.agent_eval_details, is_agent=True) # Changed here

        chartdata = {
            "cultural": {"people": people_cultural, "agent": agent_cultural},
            "visual": {"people": people_visual, "agent": agent_visual},
            "hallucination": {"people": people_hallucination, "agent": agent_hallucination}
        }

        caption_chart_data = {
            "captionId": caption.captionId,
            "title": caption.survey.title,
            "imageUrl": caption.survey.imageUrl,
            "content": caption.text,
            "chartdata": chartdata
        }
        response_data.append(caption_chart_data)

    return {
        "responseData": response_data,
        "totalPage": total_pages
    }


async def get_chart_data_for_single_caption(db: AsyncSession, caption_id: int):
    """
    단일 캡션에 대한 응답을 집계하여 차트 데이터를 조회합니다.
    """
    caption_query = select(models.Caption).options(
        selectinload(models.Caption.survey),
        selectinload(models.Caption.responses),
        selectinload(models.Caption.agent_eval_details_v2)
    ).where(models.Caption.captionId == caption_id)
    
    caption_result = await db.execute(caption_query)
    caption = caption_result.scalars().first()

    if not caption:
        return None

    # Group agent_eval_details_v2 by flag
    agent_eval_details_by_flag = {}
    for detail in caption.agent_eval_details_v2:
        if detail.flag not in agent_eval_details_by_flag:
            agent_eval_details_by_flag[detail.flag] = []
        agent_eval_details_by_flag[detail.flag].append(detail)

    chartdata = {
        "cultural": [],
        "visual": [],
        "hallucination": []
    }

    # Sort all user responses by time
    all_user_responses = sorted(caption.responses, key=lambda r: r.time)

    # For each flag, calculate wassenstein distance using the correct slice of user responses
    for flag in sorted(agent_eval_details_by_flag.keys()):
        details_for_flag = agent_eval_details_by_flag[flag]
        
        # Determine the number of user responses to use for this flag
        num_responses_to_use = 1 if flag == 0 else flag
        responses_for_flag = all_user_responses[:num_responses_to_use]

        # Generate user distribution for the current slice of responses
        user_cultural_dist = [r.cultural for r in responses_for_flag if r.cultural is not None]
        user_visual_dist = [r.visual for r in responses_for_flag if r.visual is not None]
        user_hallucination_dist = [r.hallucination for r in responses_for_flag if r.hallucination is not None]

        user_dists = {
            "cultural": user_cultural_dist,
            "visual": user_visual_dist,
            "hallucination": user_hallucination_dist
        }

        # Group agent eval details by type for the current flag
        details_by_type = {
            "cultural": [],
            "visual": [],
            "hallucination": []
        }
        for detail in details_for_flag:
            if detail.type in details_by_type:
                details_by_type[detail.type].append(detail)

        for type_name in ["cultural", "visual", "hallucination"]:
            type_details = details_by_type.get(type_name)
            user_dist = user_dists[type_name]

            if not type_details or not user_dist:
                chartdata[type_name].append(None) 
                continue

            type_details.sort(key=lambda x: x.likert)
            
            ai_values = [d.likert for d in type_details]
            ai_weights = [d.value for d in type_details]

            if not np.isclose(sum(ai_weights), 1.0):
                ai_weights_sum = sum(ai_weights)
                if ai_weights_sum > 0:
                    ai_weights = np.array(ai_weights) / ai_weights_sum
                else: # if sum is 0, treat as uniform
                    ai_weights = None 
            
            dist = wasserstein_distance(user_dist, ai_values, v_weights=ai_weights)
            
            chartdata[type_name].append(dist)


    # This function calculates the overall user distribution for the entire caption
    def calculate_user_distribution(responses):
        cultural_scores = [0] * 5
        visual_scores = [0] * 5
        hallucination_scores = [0] * 5

        for r in responses:
            if r.cultural and 1 <= r.cultural <= 5:
                cultural_scores[r.cultural - 1] += 1
            if r.visual and 1 <= r.visual <= 5:
                visual_scores[r.visual - 1] += 1
            if r.hallucination and 1 <= r.hallucination <= 5:
                hallucination_scores[r.hallucination - 1] += 1
        
        total_responses = len(responses)
        if total_responses == 0:
            return {
                "cultural": [0.0] * 5,
                "visual": [0.0] * 5,
                "hallucination": [0.0] * 5
            }

        return {
            "cultural": [round((s / total_responses) * 100, 2) for s in cultural_scores],
            "visual": [round((s / total_responses) * 100, 2) for s in visual_scores],
            "hallucination": [round((s / total_responses) * 100, 2) for s in hallucination_scores]
        }

    user_response_distribution = calculate_user_distribution(caption.responses)

    return {
        "captionId": caption.captionId,
        "title": caption.survey.title,
        "imageUrl": caption.survey.imageUrl,
        "content": caption.text,
        "chartdata": chartdata,
        "userResponseDistribution": user_response_distribution
    }
