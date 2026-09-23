from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Database operations for users.

    The repository flushes changes so generated fields are available, but leaves
    transaction commits and rollbacks to the calling service or unit of work.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.email == email).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        **extra_fields: Any,
    ) -> User:
        """Persist a user with an already-hashed password."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            **extra_fields,
        )
        self.session.add(user)
        await self.session.flush()
        return user
