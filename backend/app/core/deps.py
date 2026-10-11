from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole

# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ContributorUser = Annotated[User, Depends(require_role(UserRole.CONTRIBUTOR, UserRole.REVIEWER, UserRole.ADMIN))]
ReviewerUser = Annotated[User, Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
