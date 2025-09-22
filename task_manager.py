import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from file_handler import FileHandler
from nlp_parser import NLPParser
from exceptions import TaskNotFoundError, TaskParsingError

class Task:
    
    def __init__(self, task_id: Optional[str] = None, task_name: str = "", due_date: Optional[str] = None, 
                 due_time: Optional[str] = None, priority: str = "Medium", completed: bool = False,
                 created_at: Optional[str] = None, completed_at: Optional[str] = None):
        self.id = task_id or str(uuid.uuid4())
        self.task_name = task_name
        self.due_date = due_date
        self.due_time = due_time
        self.priority = priority
        self.completed = completed
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_name': self.task_name,
            'due_date': self.due_date,
            'due_time': self.due_time,
            'priority': self.priority,
            'completed': self.completed,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        task_data = data.copy()
        if 'id' in task_data:
            task_data['task_id'] = task_data.pop('id')
        return cls(**task_data)
    
    def is_overdue(self) -> bool:
        if not self.due_date or self.completed:
            return False
        
        try:
            due_datetime = datetime.fromisoformat(self.due_date)
            if self.due_time:
                time_str = self.due_time.replace(' ', '')
                if time_str.upper().endswith(('AM', 'PM')):
                    due_datetime = datetime.strptime(f"{self.due_date} {self.due_time}", 
                                                   "%Y-%m-%d %I:%M %p")
                else:
                    due_datetime = datetime.strptime(f"{self.due_date} {self.due_time}", 
                                                   "%Y-%m-%d %H:%M")
            return due_datetime < datetime.now()
        except (ValueError, TypeError):
            return False
    
    def is_due_today(self) -> bool:
        if not self.due_date:
            return False
        
        try:
            due_date = datetime.fromisoformat(self.due_date).date()
            return due_date == datetime.now().date()
        except (ValueError, TypeError):
            return False

class TaskManager:
    
    def __init__(self, filename: str = "tasks.json"):
        self.file_handler = FileHandler(filename)
        self.nlp_parser = NLPParser()
        self.tasks: List[Task] = self._load_tasks()
    
    def _load_tasks(self) -> List[Task]:
        task_dicts = self.file_handler.load_tasks()
        return [Task.from_dict(task_dict) for task_dict in task_dicts]
    
    def _save_tasks(self):
        task_dicts = [task.to_dict() for task in self.tasks]
        self.file_handler.save_tasks(task_dicts)
    
    def add_task_from_text(self, input_text: str) -> Task:
        try:
            parsed_data = self.nlp_parser.parse_task(input_text)
            
            task = Task(
                task_name=parsed_data.get('task_name') or 'New task',
                due_date=parsed_data.get('due_date'),
                due_time=parsed_data.get('due_time'),
                priority=parsed_data.get('priority') or 'Medium'
            )
            
            self.tasks.append(task)
            self._save_tasks()
            return task
            
        except Exception as e:
            raise TaskParsingError(f"Failed to create task from input: {str(e)}")
    
    def add_task(self, task_name: str, due_date: Optional[str] = None, due_time: Optional[str] = None, 
                priority: str = "Medium") -> Task:
        task = Task(
            task_name=task_name,
            due_date=due_date,
            due_time=due_time,
            priority=priority
        )
        
        self.tasks.append(task)
        self._save_tasks()
        return task
    
    def get_task(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
    
    def update_task(self, task_id: str, **kwargs) -> Task:
        task = self.get_task(task_id)
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self._save_tasks()
        return task
    
    def delete_task(self, task_id: str):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self._save_tasks()
    
    def complete_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        task.completed = True
        task.completed_at = datetime.now().isoformat()
        self._save_tasks()
        return task
    
    def get_all_tasks(self) -> List[Task]:
        return self.tasks.copy()
    
    def get_pending_tasks(self) -> List[Task]:
        return [task for task in self.tasks if not task.completed]
    
    def get_completed_tasks(self) -> List[Task]:
        return [task for task in self.tasks if task.completed]
    
    def get_overdue_tasks(self) -> List[Task]:
        return [task for task in self.tasks if task.is_overdue()]
    
    def get_today_tasks(self) -> List[Task]:
        return [task for task in self.tasks if task.is_due_today()]
    
    def get_upcoming_tasks(self, days: int = 7) -> List[Task]:
        cutoff_date = datetime.now() + timedelta(days=days)
        upcoming_tasks = []
        
        for task in self.tasks:
            if task.completed or not task.due_date:
                continue
            
            try:
                due_date = datetime.fromisoformat(task.due_date)
                if due_date <= cutoff_date:
                    upcoming_tasks.append(task)
            except (ValueError, TypeError):
                continue
        
        return upcoming_tasks
    
    def search_tasks(self, query: str) -> List[Task]:
        query_lower = query.lower()
        return [task for task in self.tasks 
                if query_lower in task.task_name.lower()]
    
    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        return [task for task in self.tasks if task.priority == priority]
    
    def get_task_stats(self) -> Dict[str, int]:
        return {
            'total': len(self.tasks),
            'pending': len(self.get_pending_tasks()),
            'completed': len(self.get_completed_tasks()),
            'overdue': len(self.get_overdue_tasks()),
            'due_today': len(self.get_today_tasks())
        }