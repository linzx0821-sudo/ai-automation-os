from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    # Import models before metadata creation. Alembic owns production schema upgrades;
    # create_all keeps local/test startup friction low.
    from app.models.artifact import TaskArtifactModel  # noqa: F401
    from app.models.investment import (  # noqa: F401
        CompanyModel,
        DocumentModel,
        FactModel,
        FactSourceModel,
        FinancialMetricModel,
        InvestmentThesisModel,
        ThesisConditionModel,
    )
    from app.models.task import TaskEventModel, TaskModel  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
