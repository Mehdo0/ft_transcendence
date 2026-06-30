import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.database import SessionLocal
from models.models import UserModel


@pytest.fixture(autouse=True)
def _clean_test_users():
    with SessionLocal() as session:
        for user in session.query(UserModel).filter(
            UserModel.username.like("t_%")
        ).all():
            session.delete(user)
        for user in session.query(UserModel).filter(
            UserModel.username.like("db_test_%")
        ).all():
            session.delete(user)
        for user in session.query(UserModel).filter(
            UserModel.username.like("test_%")
        ).all():
            session.delete(user)
        session.commit()
