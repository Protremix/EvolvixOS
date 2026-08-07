from uuid import UUID
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def create(self, db: Session, project_create: ProjectCreate, owner_id: str | UUID) -> Project:
        project = Project(
            name=project_create.name,
            description=project_create.description,
            owner_id=owner_id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def get(self, db: Session, project_id: str | UUID) -> Project | None:
        return db.query(Project).filter(Project.id == project_id, Project.status != "deleted").first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[Project]:
        return db.query(Project).filter(Project.status != "deleted").offset(skip).limit(limit).all()

    def update(self, db: Session, project_id: str | UUID, project_update: ProjectUpdate) -> Project | None:
        project = self.get(db, project_id)
        if not project:
            return None
        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        db.commit()
        db.refresh(project)
        return project

    def delete(self, db: Session, project_id: str | UUID) -> bool:
        project = self.get(db, project_id)
        if not project:
            return False
        project.status = "deleted"
        db.commit()
        return True


project_service = ProjectService()
