import json
import os
from typing import List, Dict, Any
from exceptions import FileOperationError

class FileHandler:
    
    def __init__(self, filename: str = "tasks.json"):
        self.filename = filename
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        if not os.path.exists(self.filename):
            try:
                self.save_tasks([])
            except Exception as e:
                raise FileOperationError(f"Failed to create tasks file: {str(e)}")
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise FileOperationError(f"Invalid JSON in tasks file: {str(e)}")
        except FileNotFoundError:
            return []
        except Exception as e:
            raise FileOperationError(f"Failed to load tasks: {str(e)}")
    
    def save_tasks(self, tasks: List[Dict[str, Any]]):
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump(tasks, file, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FileOperationError(f"Failed to save tasks: {str(e)}")
    
    def backup_tasks(self) -> str:
        backup_filename = f"{self.filename}.backup"
        try:
            tasks = self.load_tasks()
            with open(backup_filename, 'w', encoding='utf-8') as file:
                json.dump(tasks, file, indent=2, ensure_ascii=False)
            return backup_filename
        except Exception as e:
            raise FileOperationError(f"Failed to create backup: {str(e)}")
    
    def restore_from_backup(self, backup_filename: str):
        try:
            if not os.path.exists(backup_filename):
                raise FileOperationError("Backup file not found")
            
            with open(backup_filename, 'r', encoding='utf-8') as file:
                tasks = json.load(file)
            
            self.save_tasks(tasks)
        except Exception as e:
            raise FileOperationError(f"Failed to restore from backup: {str(e)}")