from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL=(
  "postgresql+psycopg://neondb_owner:npg_Rlh01mvQcZWO@ep-empty-water-aok7il1c-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

engine = create_engine(
  DATABASE_URL,
  echo=True
)

SessionLocal = sessionmaker(
  bind=engine,
  autoflush=False,
  autocommit=False,
)

