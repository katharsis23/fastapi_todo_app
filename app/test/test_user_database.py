from database.user import (
    find_user_by_id,
    create_user,
    authenticate_user
)
import uuid
import asyncio
import pytest
from schemas.user import UserLogin, UserSchema

def create_uuid():
    return str(uuid.uuid4).replace("-","")

USER_ID = create_uuid
USERNAME = "test_user"
PASSWORD = "123456789"


@pytest.fixture(autouse=True)
def create_mocked_user():
    # TODO
    #Create fixture to insert user in database
    pass


@pytest.mark.asyncio
def test_create_user():
    user = UserSchema(
        username=USERNAME,
        password=PASSWORD,
    )
    pass