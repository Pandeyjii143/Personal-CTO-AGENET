from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return a user by primary key, or None if no user exists."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return a user by email address, or None if no user exists."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, *, email: str, hashed_password: str) -> User:
    """Persist a user using an already-hashed password; never pass a raw password."""
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user
