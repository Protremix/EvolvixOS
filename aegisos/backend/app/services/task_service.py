from uuid import UUID
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def create(self, db: Session, task_create: TaskCreate) -> Task:
        task = Task(
            title=task_create.title,
            description=task_create.description,
            project_id=task_create.project_id,
            priority=task_create.priority,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get(self, db: Session, task_id: str | UUID) -> Task | None:
        return db.query(Task).filter(Task.id == task_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100, project_id: str | UUID | None = None) -> list[Task]:
        query = db.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        return query.offset(skip).limit(limit).all()

    def update(self, db: Session, task_id: str | UUID, task_update: TaskUpdate) -> Task | None:
        task = self.get(db, task_id)
        if not task:
            return None
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task_id: str | UUID) -> bool:
        task = self.get(db, task_id)
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True


task_service = TaskService()
