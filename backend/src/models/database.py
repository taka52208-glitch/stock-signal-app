from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# psycopg3ドライバーを使用するためURLを変換
db_url = settings.database_url or 'sqlite:///./stock.db'
if db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
print(f"[database] Using: {db_url[:30]}...")

engine_args = {}
if 'sqlite' in db_url:
    engine_args['connect_args'] = {'check_same_thread': False}
else:
    engine_args['pool_pre_ping'] = True
    engine_args['pool_recycle'] = 300

engine = create_engine(db_url, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
