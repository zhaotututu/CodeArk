from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool

# Use SQLite for simplicity. 
# check_same_thread=False is needed for FastAPI's async environment with SQLite
sqlite_file_name = "tutu_code_ark_v1.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

