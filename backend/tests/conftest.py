"""
Configuración global de pytest para IntellectClone.
Los fixtures de base de datos y cliente HTTP se definen en Fase B.
"""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
