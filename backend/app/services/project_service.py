from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate

class ProjectService:
    def create_project(self, db: Session, project_in: ProjectCreate) -> Project:
        db_project = Project(
            name=project_in.name,
            description=project_in.description
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    def get_projects(self, db: Session, skip: int = 0, limit: int = 100) -> list[Project]:
        return db.query(Project).offset(skip).limit(limit).all()

    def get_project(self, db: Session, project_id: int) -> Project | None:
        return db.query(Project).filter(Project.id == project_id).first()

    def update_project(self, db: Session, db_project: Project, project_in: ProjectCreate) -> Project:
        db_project.name = project_in.name
        db_project.description = project_in.description
        db.commit()
        db.refresh(db_project)
        return db_project

    def delete_project(self, db: Session, db_project: Project) -> Project:
        db.delete(db_project)
        db.commit()
        return db_project

project_service = ProjectService()
