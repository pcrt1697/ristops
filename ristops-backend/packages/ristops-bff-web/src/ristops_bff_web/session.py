from redis.asyncio import Redis
from starlette.requests import Request
from starsessions import get_session_id, load_session

from ristops_bff_web.context import BffContextKey
from ristops_bff_web.settings import BffSettings
from ristops_lib_core.context import ContextKey, APP_CONTEXT
from ristops_lib_core.schema.authn import LoginResponse


class SessionField:
    USER_ID = "user_id"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"


def get_redis_client():
    bff_settings = BffSettings.get()
    return Redis.from_url(bff_settings.redis_url)


def update_context(request: Request) -> None:
    """ Update context from request session """
    session_id = get_session_id(request)
    APP_CONTEXT.set(BffContextKey.SESSION_ID, session_id)
    user_id = request.session.get(SessionField.USER_ID)
    APP_CONTEXT.set(ContextKey.USER_ID, user_id)
    access_token = request.session.get(SessionField.ACCESS_TOKEN)
    APP_CONTEXT.set(ContextKey.JWT, access_token)


async def save_session(login_response: LoginResponse, http_request: Request) -> None:
    await load_session(http_request)
    http_request.session[SessionField.USER_ID] = login_response.user_id
    http_request.session[SessionField.ACCESS_TOKEN] = login_response.access_token
    http_request.session[SessionField.REFRESH_TOKEN] = login_response.refresh_token
    update_context(http_request)
