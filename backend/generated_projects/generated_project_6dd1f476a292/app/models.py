from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, Float, Integer, String
from sqlalchemy.orm import declarative_base, validates

Base = declarative_base()


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    date = Column(Date, nullable=False, default=date.today)

    @validates("amount")
    def validate_amount(self, key, value):
        amount = float(value)
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
        return amount
