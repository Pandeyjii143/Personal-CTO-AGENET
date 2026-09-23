from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Persistence operations for user accounts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: Any) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        result = await self.session.execute(
            select(User).where(User.email == normalized_email)
        )
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.email == email.strip().lower()).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, **user_data: Any) -> User:
        if isinstance(user_data.get("email"), str):
            user_data["email"] = user_data["email"].strip().lower()

        user = User(**user_data)
        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            raise
        return user

    async def update(
        self, user: User, update_data: Mapping[str, Any]
    ) -> User:
        column_names = {attribute.key for attribute in User.__mapper__.column_attrs}
        for key, value in update_data.items():
            if key in column_names and key != "id":
                if key == "email" and isinstance(value, str):
                    value = value.strip().lower()
                setattr(user, key, value)

        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            raise
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
