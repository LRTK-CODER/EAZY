from sqlalchemy.orm import Session
from app.models.target import Target
from app.schemas.target import TargetCreate, TargetUpdate

class TargetService:
    def get_target(self, db: Session, target_id: int) -> Target | None:
        return db.query(Target).filter(Target.id == target_id).first()

    def update_target(self, db: Session, db_target: Target, target_in: TargetUpdate) -> Target:
        if target_in.name is not None:
            db_target.name = target_in.name
        db.commit()
        db.refresh(db_target)
        return db_target

    def delete_target(self, db: Session, db_target: Target) -> Target:
        db.delete(db_target)
        db.commit()
        return db_target

    def create_target(self, db: Session, project_id: int, target_in: TargetCreate) -> Target:
        db_target = Target(
            project_id=project_id,
            name=target_in.name,
            url=target_in.url
        )
        db.add(db_target)
        db.commit()
        db.refresh(db_target)
        return db_target

    def get_targets(self, db: Session, project_id: int, skip: int = 0, limit: int = 100) -> list[Target]:
        return db.query(Target).filter(Target.project_id == project_id).offset(skip).limit(limit).all()

target_service = TargetService()
