from app.core.db import SessionLocal
from app.models.target import Target
from app.models.project import Project
from app.models.scan import ScanJob
from app.models.llm_config import LLMConfig

def check_target():
    db = SessionLocal()
    try:
        t = db.query(Target).filter(Target.id == 1).first()
        if t:
            print(f"Target 1 exists: {t.name} ({t.url})")
        else:
            print("Target 1 DOES NOT exist.")
            # Verify if ANY target exists
            all_t = db.query(Target).all()
            print(f"Total targets: {len(all_t)}")
            for x in all_t:
                 print(f" - {x.id}: {x.name}")

    finally:
        db.close()

if __name__ == "__main__":
    check_target()
