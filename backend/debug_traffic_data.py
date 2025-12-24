from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.traffic_log import TrafficLog
from app.models.target import Target
from app.models.project import Project
from app.models.llm_config import LLMConfig
from app.models.scan import ScanJob
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

target_id = 17 # From user screenshot

print(f"--- Checking Traffic Logs for Target {target_id} ---")

# 1. Count logs
count = db.query(TrafficLog).filter(TrafficLog.target_id == target_id).count()
print(f"Total Logs: {count}")

# 2. Check Host distribution
from sqlalchemy import func
hosts = db.query(TrafficLog.host, func.count(TrafficLog.id)).filter(TrafficLog.target_id == target_id).group_by(TrafficLog.host).all()
print("\n--- distinct Hosts ---")
for h, c in hosts:
    print(f"'{h}': {c}")

# 3. Sample logs with empty host
empty_host = db.query(TrafficLog).filter(TrafficLog.target_id == target_id, TrafficLog.host == "").limit(5).all()
if empty_host:
    print("\n--- Sample Logs with Empty Host ---")
    for log in empty_host:
        print(f"ID: {log.id}, URL: {log.url}, Method: {log.method}")

db.close()
