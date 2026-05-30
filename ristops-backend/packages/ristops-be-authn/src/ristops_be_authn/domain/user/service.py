import logging
from functools import lru_cache
from http import HTTPStatus
from uuid import UUID, uuid5, uuid4

from argon2 import PasswordHasher
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_authn.domain.user.entities import UserEntity
from ristops_be_authn.domain.user.schema import UserUpdateRequest
from ristops_be_authn.services.user import publish_user_created_event, publish_user_deleted_event
from ristops_be_authn.settings import Argon2Settings
from ristops_lib_core.auth.authn import RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.user import UserCreationRequest
from ristops_lib_sql.engine import get_sql_session

_logger = logging.getLogger(__name__)
_admin_id = uuid5(RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME)


@lru_cache(maxsize=1)
def _get_password_hasher() -> PasswordHasher:
    settings = Argon2Settings.get()
    return PasswordHasher(
        time_cost=settings.time_cost,
        memory_cost=settings.memory_cost,
        parallelism=settings.parallelism,
        hash_len=settings.hash_len,
        salt_len=settings.salt_len,
    )


def _hash_password(password: str) -> str:
    """ Hash password and return hashed password. """
    return _get_password_hasher().hash(password)


def _verify_password(password: str, hashed: str) -> None:
    """ Verify if password matches hashed password; if not, throw HTTP unauthorized error. """
    if not _do_verify_password(password, hashed):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials")


def _do_verify_password(password: str, hashed: str) -> bool:
    """ Verify if password matches hashed password. """
    try:
        return _get_password_hasher().verify(hashed, password)
    except Exception as e:
        _logger.exception(f"Password verification failed: {e}")
        return False


def _needs_rehash(hashed: str) -> bool:
    """ Check if params changed. """
    return _get_password_hasher().check_needs_rehash(hashed)


async def _create_user(user_id: UUID, request: UserCreationRequest) -> UserEntity:
    """ Create new user using the provided user ID. """
    session = get_sql_session()
    password = _hash_password(request.password.get_secret_value())
    user = UserEntity(
        id=user_id,
        username=request.username.lower(),
        display_name=request.display_name,
        email=request.email.lower(),
        password=password,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    await publish_user_created_event(user_id)
    _logger.info(f"Created user: {user.id}")
    return user


async def create_user(request: UserCreationRequest) -> UserEntity:
    """ Create new user. """
    await throw_if_exists_by_username(request.username)
    await throw_if_exists_by_email(request.email)
    user_id = uuid4()
    user = await _create_user(user_id, request)
    return user


async def throw_if_exists_by_username(username: str):
    already_exists = await _exists_user_by(UserEntity.username == username)
    if already_exists:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Username already taken"
        )


async def throw_if_exists_by_email(email: str):
    already_exists = await _exists_user_by(UserEntity.email == email.lower())
    if already_exists:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Email already taken"
        )


async def update_user(user_id: UUID, request: UserUpdateRequest) -> UserEntity:
    """ Update user. Unset fields are not updated. """

    user = await find_user_or_throw(user_id)

    fields_to_update = request.model_fields_set
    # TODO: use `field in fields_to_update` consistently for all fields instead of `is not None`,
    #  so that explicitly sending null is handled correctly for every optional field.
    if request.username is not None:
        await throw_if_exists_by_username(request.username)
        user.username = request.username.lower()
    if request.email is not None:
        await throw_if_exists_by_email(request.email)
        user.email = request.email.lower()
    if request.password is not None:
        password = _hash_password(request.password.get_secret_value())
        user.password = password
    if "display_name" in fields_to_update:
        # no None check because its nullable
        user.display_name = request.display_name

    session = get_sql_session()
    await session.flush()
    await session.refresh(user)
    _logger.info(f"Updated user: {user.id}")
    return user


async def find_user_by_email_or_throw(email: str) -> UserEntity:
    """ Find user by email or throw not found HTTP exception. """
    return await _find_user_by_or_throw(UserEntity.email == email)


async def find_user_or_throw(user_id: UUID) -> UserEntity:
    """ Find user by id or throw not found HTTP exception. """
    return await _find_user_by_or_throw(UserEntity.id == str(user_id))


async def find_user(user_id: UUID) -> UserEntity | None:
    """ Find user by id or throw not found HTTP exception. """
    return await _find_user_by(UserEntity.id == str(user_id))


async def _find_user_by(query: ColumnElement[bool]) -> UserEntity | None:
    """ Lookup user using input query. """
    session = get_sql_session()
    result: ScalarResult[UserEntity] = await session.scalars(
        select(UserEntity).where(query).limit(1)
    )
    return result.one_or_none()


async def _exists_user_by(query: ColumnElement[bool]) -> bool:
    """ Lookup user using input query and returns True if exists. """
    user = await _find_user_by(query)
    return user is not None


async def _find_user_by_or_throw(query: ColumnElement[bool]) -> UserEntity:
    """ Lookup user using input query or throw not found HTTP exception. """
    user = await _find_user_by(query)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found",
        )
    return user


async def find_me() -> UserEntity:
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    return await find_user_or_throw(user_id)


async def authenticate_user(email: str, password: str) -> str:
    """ Validates user password and returns user id. """
    user = await find_user_by_email_or_throw(email)
    _verify_password(password, user.password)
    if _needs_rehash(hashed=user.password):
        session = get_sql_session()
        user.password = _hash_password(password)
        await session.flush()
        await session.refresh(user)
    return str(user.id)


async def throw_if_user_not_exists(user_id: UUID) -> None:
    """ Throw an error if user doesn't exist. """
    exists = await _exists_user_by(UserEntity.id == user_id)
    if not exists:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found",
        )


async def create_or_update_admin(
        username: str,
        display_name: str | None,
        email: str,
        password: str,
) -> None:
    """ Create admin user if not exists. """

    user = await find_user(_admin_id)
    if user is None:
        request = UserCreationRequest(
            username=username,
            display_name=display_name,
            email=email,
            password=SecretStr(password),
        )
        await _create_user(_admin_id, request)
        return None

    request = UserUpdateRequest(
        username=username,
        display_name=display_name,
        email=email,
        password=SecretStr(password),
    )
    await update_user(user.id, request)
    return None


async def remove_me() -> None:
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    await remove_user(user_id)


async def remove_user(user_id: UUID) -> None:
    user = await find_user_or_throw(user_id)
    session = get_sql_session()
    await session.delete(user)
    await publish_user_deleted_event(user_id)
