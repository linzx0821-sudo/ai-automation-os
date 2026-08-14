from functools import lru_cache

from app.core.config import get_settings
from app.services.codex_gateway import CodexGateway, build_codex_gateway


@lru_cache
def _gateway_singleton() -> CodexGateway:
    return build_codex_gateway(get_settings())


def get_codex_gateway() -> CodexGateway:
    return _gateway_singleton()
