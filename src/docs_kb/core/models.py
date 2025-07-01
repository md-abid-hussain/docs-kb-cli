from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlmodel import (
    JSON,
    Column,
    DateTime,
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
)


class Repository(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    branch: str = Field(default="main")
    knowledge_base_name: str
    created_at: datetime = Field(
        default_factory=datetime.now, sa_column=Column(DateTime, default=datetime.now)
    )
    last_ingested: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    files: List[Dict[str, str]] = Field(default=[], sa_column=Column(JSON))


# Use SQLite instead of PostgreSQL
def get_database_path():
    """Get database path in user's home directory or project directory"""
    home_dir = Path.home()
    db_dir = home_dir / ".docs-kb"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "docs_kb.db"


# Create SQLite engine
sqlite_url = f"sqlite:///{get_database_path()}"
engine = create_engine(sqlite_url)


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        raise e


def get_session():
    """Get a database session."""
    return Session(engine)


def add_repository(
    name: str,
    knowledge_base_name: str,
    branch: str = "main",
    files: List[Dict[str, str]] = None,
) -> Repository:
    """Add a new repository to the database."""
    with get_session() as session:
        # Create new repository
        repository = Repository(
            name=name,
            branch=branch,
            knowledge_base_name=knowledge_base_name,
            files=files or [],
        )

        session.add(repository)
        session.commit()
        session.refresh(repository)
        return repository


def get_repository_by_name(name: str) -> Optional[Repository]:
    """Get repository by name."""
    with get_session() as session:
        statement = select(Repository).filter(Repository.name == name)
        repository = session.exec(statement).first()
        if repository:
            return repository
        return None


def list_repositories() -> List[Repository]:
    """List all repositories."""
    with get_session() as session:
        statement = select(Repository)
        repositories = session.exec(statement).all()
        return repositories


def delete_repository(name: str) -> bool:
    """Delete a repository by name."""
    with get_session() as session:
        statement = select(Repository).filter(Repository.name == name)
        repository = session.exec(statement).first()
        if not repository:
            return False
        session.delete(repository)
        session.commit()
        return True
