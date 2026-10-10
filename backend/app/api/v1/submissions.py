import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DbSession, CurrentUser, ReviewerUser
from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate, SubmissionRead, SubmissionReview

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreate, db: DbSession, user: CurrentUser
) -> SubmissionRead:
    submission = Submission(
        contributor_id=user.id,
        submission_type=payload.submission_type,
        title=payload.title,
        payload=payload.payload,
    )
    db.add(submission)
    await db.flush()
    return SubmissionRead.model_validate(submission)


@router.get("", response_model=list[SubmissionRead])
async def list_submissions(
    db: DbSession, _: ReviewerUser, status_filter: str | None = None
) -> list[SubmissionRead]:
    stmt = select(Submission).order_by(Submission.created_at.desc())
    if status_filter:
        stmt = stmt.where(Submission.status == status_filter)
    result = await db.execute(stmt)
    return [SubmissionRead.model_validate(s) for s in result.scalars().all()]


@router.post("/{submission_id}/review", response_model=SubmissionRead)
async def review_submission(
    submission_id: uuid.UUID, payload: SubmissionReview, db: DbSession, user: ReviewerUser
) -> SubmissionRead:
    submission = await db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission.status = payload.status
    submission.reviewer_notes = payload.reviewer_notes
    submission.reviewer_id = user.id
    await db.flush()
    return SubmissionRead.model_validate(submission)