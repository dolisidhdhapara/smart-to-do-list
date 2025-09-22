class TaskParsingError(Exception):
    def __init__(self, message="Failed to parse task from natural language input"):
        self.message = message
        super().__init__(self.message)

class InvalidDateTimeError(Exception):
    def __init__(self, message="Invalid date or time format"):
        self.message = message
        super().__init__(self.message)

class FileOperationError(Exception):
    def __init__(self, message="File operation failed"):
        self.message = message
        super().__init__(self.message)

class APIError(Exception):
    def __init__(self, message="API request failed"):
        self.message = message
        super().__init__(self.message)

class TaskNotFoundError(Exception):
    def __init__(self, message="Task not found"):
        self.message = message
        super().__init__(self.message)