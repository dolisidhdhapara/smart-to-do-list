import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from exceptions import TaskParsingError, InvalidDateTimeError

class NLPParser:
    
    def __init__(self):
        # Time
        self.time_patterns = [
            r'at (\d{1,2}):(\d{2})\s*(am|pm)',
            r'at (\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(am|pm)'
        ]
        
        # Date
        self.date_patterns = [
            r'(today)',
            r'(tomorrow)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)'
        ]
        
        # Priority
        self.priority_patterns = [
            r'(high|urgent|important|priority)',
            r'(low|minor)',
            r'(medium|normal)'
        ]
        
        # Common task
        self.action_words = ['submit', 'call', 'meet', 'finish', 'complete', 'buy', 'send', 'write', 'read', 'study', 'work', 'visit']
    
    def parse_task(self, input_text: str) -> Dict[str, Optional[str]]:
        try:
            if not input_text or not input_text.strip():
                raise TaskParsingError("Empty input text")
            
            input_text = input_text.strip().lower()
            
            # time
            time_info = self._extract_time(input_text)
            
            # date
            date_info = self._extract_date(input_text)
            
            # priority
            priority = self._extract_priority(input_text)
            
            # Task name (remove time, date, and priority keywords)
            task_name = self._extract_task_name(input_text, time_info, date_info, priority)
            
            return {
                'task_name': task_name,
                'due_date': date_info,
                'due_time': time_info,
                'priority': priority
            }
            
        except Exception as e:
            raise TaskParsingError(f"Failed to parse task: {str(e)}")
    
    def _extract_time(self, text: str) -> Optional[str]:
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Hour, minute, am/pm
                    hour, minute, period = groups
                    return f"{hour}:{minute} {period.upper()}"
                elif len(groups) == 2:
                    if groups[1].lower() in ['am', 'pm']:  # Hour, am/pm
                        hour, period = groups
                        return f"{hour}:00 {period.upper()}"
                    else:  # Hour, minute (24-hour format)
                        hour, minute = groups
                        return f"{hour}:{minute}"
                elif len(groups) == 1:  
                    if groups[0].lower() in ['am', 'pm']:
                        return None
                    return groups[0]
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        today = datetime.now()
        
        if 'today' in text:
            return today.strftime('%Y-%m-%d')
        elif 'tomorrow' in text:
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in text:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:  
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
        
        for pattern in self.date_patterns[3:]:  
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return self._parse_date_match(match, today)
                except:
                    continue
        
        return None
    
    def _parse_date_match(self, match, today: datetime) -> Optional[str]:
        groups = match.groups()
        
        if len(groups) == 3 and groups[0].isdigit():
            month, day, year = groups
            if len(year) == 2:
                year = f"20{year}"
            date = datetime(int(year), int(month), int(day))
            return date.strftime('%Y-%m-%d')
        
        elif len(groups) == 2:
            months = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            if groups[0].isdigit():  
                day, month_name = groups
                month = months.get(month_name.lower())
            else:  
                month_name, day = groups
                month = months.get(month_name.lower())
            
            if month:
                year = today.year
                date = datetime(year, month, int(day))
                if date < today:  
                    date = datetime(year + 1, month, int(day))
                return date.strftime('%Y-%m-%d')
        
        return None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        if re.search(r'\b(high|urgent|important|priority)\b', text, re.IGNORECASE):
            return 'High'
        elif re.search(r'\b(low|minor)\b', text, re.IGNORECASE):
            return 'Low'
        elif re.search(r'\b(medium|normal)\b', text, re.IGNORECASE):
            return 'Medium'
        return 'Medium'  # Default priority
    
    def _extract_task_name(self, text: str, time_info: Optional[str], 
                          date_info: Optional[str], priority: Optional[str]) -> str:
        keywords_to_remove = [
            r'\bat \d{1,2}:?\d{0,2}\s*(am|pm)?\b',
            r'\b(today|tomorrow)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b',
            r'\b\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(high|urgent|important|priority|low|minor|medium|normal)\b',
            r'\bby\b',
            r'\bon\b'
        ]
        
        cleaned_text = text
        for pattern in keywords_to_remove:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        if cleaned_text:
            return cleaned_text.capitalize()
        
        return "New task"