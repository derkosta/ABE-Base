"""
E-number parsing and normalization utilities
"""
import re
from typing import List, Optional, Tuple

class ENumberParser:
    """Parser for E-approval numbers with tolerance for various formats"""
    
    # Regex patterns for E-numbers
    ENUMBER_PATTERNS = [
        # Standard format: e13*1234*5678*00
        r'[eE](\d+)\*?(\d+)\*?(\d+)\*?(\d+)',
        # Alternative with spaces/hyphens: e13-1234-5678-00
        r'[eE](\d+)[\s\-]*(\d+)[\s\-]*(\d+)[\s\-]*(\d+)',
        # Simple format: e13 1234 5678 00
        r'[eE](\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        # Compact format: e131234567800
        r'[eE](\d{2})(\d{4})(\d{4})(\d{2})',
    ]
    
    @classmethod
    def extract_enumbers(cls, text: str) -> List[str]:
        """Extract all E-numbers from text"""
        if not text:
            return []
        
        enumbers = set()
        
        for pattern in cls.ENUMBER_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract groups
                authority = match.group(1).zfill(2)
                base = match.group(2).zfill(4)
                ext = match.group(3).zfill(4)
                rev = match.group(4).zfill(2)
                
                # Create normalized E-number
                enumber = f"e{authority}*{base}*{ext}*{rev}"
                enumbers.add(enumber.lower())
        
        return list(enumbers)
    
    @classmethod
    def normalize_enumber(cls, enumber: str) -> Optional[str]:
        """Normalize an E-number to canonical format"""
        if not enumber:
            return None
        
        # Clean input
        cleaned = re.sub(r'[^\d\*\-eE\s]', '', enumber.strip())
        
        for pattern in cls.ENUMBER_PATTERNS:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                authority = match.group(1).zfill(2)
                base = match.group(2).zfill(4)
                ext = match.group(3).zfill(4)
                rev = match.group(4).zfill(2)
                
                return f"e{authority}*{base}*{ext}*{rev}".lower()
        
        return None
    
    @classmethod
    def parse_enumber(cls, enumber: str) -> Optional[Tuple[int, int, int, int]]:
        """Parse E-number into components (authority, base, ext, rev)"""
        normalized = cls.normalize_enumber(enumber)
        if not normalized:
            return None
        
        # Extract from normalized format e13*1234*5678*00
        match = re.match(r'e(\d{2})\*(\d{4})\*(\d{4})\*(\d{2})', normalized)
        if match:
            return (
                int(match.group(1)),  # authority
                int(match.group(2)),  # base
                int(match.group(3)),  # ext
                int(match.group(4))   # rev
            )
        
        return None
    
    @classmethod
    def is_enumber(cls, text: str) -> bool:
        """Check if text contains an E-number"""
        return len(cls.extract_enumbers(text)) > 0
    
    @classmethod
    def fuzzy_match_enumbers(cls, query_enumbers: List[str], doc_enumbers: List[str], tolerance: float = 0.8) -> bool:
        """Check if query E-numbers fuzzy match document E-numbers"""
        if not query_enumbers or not doc_enumbers:
            return False
        
        # Normalize all E-numbers
        norm_query = [cls.normalize_enumber(e) for e in query_enumbers if cls.normalize_enumber(e)]
        norm_doc = [cls.normalize_enumber(e) for e in doc_enumbers if cls.normalize_enumber(e)]
        
        if not norm_query or not norm_doc:
            return False
        
        # Check for exact matches first
        for q_e in norm_query:
            if q_e in norm_doc:
                return True
        
        # For fuzzy matching, we could implement more sophisticated algorithms
        # For now, we'll do partial matching (e.g., match if authority and base are the same)
        for q_e in norm_query:
            q_parts = cls.parse_enumber(q_e)
            if not q_parts:
                continue
            
            for d_e in norm_doc:
                d_parts = cls.parse_enumber(d_e)
                if not d_parts:
                    continue
                
                # Check if authority and base match (tolerance for extension/revision differences)
                if q_parts[0] == d_parts[0] and q_parts[1] == d_parts[1]:
                    return True
        
        return False

# Global parser instance
enumber_parser = ENumberParser()
