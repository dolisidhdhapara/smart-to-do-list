import requests
import threading
from typing import Optional, Callable, Dict
from exceptions import APIError

class APIHandler:
    
    def __init__(self):
        self.quote_apis = [
            "https://zenquotes.io/api/random",
            "https://api.quotable.io/random"
        ]
        self.timeout = 5
        self.fallback_quotes = [
            "The way to get started is to quit talking and begin doing. - Walt Disney",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill"
        ]
    
    def get_motivational_quote(self, callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        if callback:
            thread = threading.Thread(target=self._async_get_quote, args=(callback,))
            thread.daemon = True
            thread.start()
            return None
        else:
            return self._get_quote_sync()
    
    def _get_quote_sync(self) -> str:
        for api_url in self.quote_apis:
            try:
                response = requests.get(api_url, timeout=self.timeout)
                response.raise_for_status()
                
                quote_data = response.json()
                quote_text = self._parse_quote_response(quote_data, api_url)
                
                if quote_text:
                    return quote_text
                    
            except Exception as e:
                continue
        
        # Fallback quote if all APIs fail
        import random
        return random.choice(self.fallback_quotes)
    
    def _async_get_quote(self, callback: Callable[[str], None]):
        try:
            quote = self._get_quote_sync()
            callback(quote)
        except Exception as e:
            import random
            callback(random.choice(self.fallback_quotes))
    
    def _parse_quote_response(self, data, api_url: str) -> Optional[str]:
        try:
            if "zenquotes.io" in api_url:
                if isinstance(data, list) and len(data) > 0:
                    quote = data[0].get('q', '')
                    author = data[0].get('a', '')
                    if author and author != 'zenquotes.io':
                        return f"{quote} - {author}"
                    return quote
            
            elif "quotable.io" in api_url:
                if isinstance(data, dict):
                    quote = data.get('content', '')
                    author = data.get('author', '')
                    if author:
                        return f"{quote} - {author}"
                    return quote
            
        except Exception:
            pass
        
        return None
    
    def test_api_connection(self) -> Dict[str, bool]:
        results = {}
        for api_url in self.quote_apis:
            try:
                response = requests.get(api_url, timeout=self.timeout)
                results[api_url] = response.status_code == 200
            except Exception:
                results[api_url] = False
        return results