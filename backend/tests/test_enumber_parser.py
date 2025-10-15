"""
Tests for E-number parser functionality
"""
import pytest
from app.core.enumber_parser import ENumberParser


class TestENumberParser:
    """Test cases for E-number parsing and normalization"""

    def test_extract_enumbers_standard_format(self):
        """Test extraction of standard E-number format"""
        text = "This document contains e13*1234*5678*00 and e1*2345*6789*01"
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 2
        assert "e13*1234*5678*00" in enumbers
        assert "e01*2345*6789*01" in enumbers

    def test_extract_enumbers_with_spaces(self):
        """Test extraction of E-numbers with spaces"""
        text = "E13 1234 5678 00 and e1 2345 6789 01"
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 2
        assert "e13*1234*5678*00" in enumbers
        assert "e01*2345*6789*01" in enumbers

    def test_extract_enumbers_with_hyphens(self):
        """Test extraction of E-numbers with hyphens"""
        text = "E13-1234-5678-00 and e1-2345-6789-01"
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 2
        assert "e13*1234*5678*00" in enumbers
        assert "e01*2345*6789*01" in enumbers

    def test_extract_enumbers_compact_format(self):
        """Test extraction of compact E-number format"""
        text = "e131234567800 and e012345678901"
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 2
        assert "e13*1234*5678*00" in enumbers
        assert "e01*2345*6789*01" in enumbers

    def test_extract_enumbers_case_insensitive(self):
        """Test extraction is case insensitive"""
        text = "E13*1234*5678*00 and E13*1234*5678*00"
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 1  # Duplicates should be removed
        assert "e13*1234*5678*00" in enumbers

    def test_normalize_enumber_standard(self):
        """Test normalization of standard E-number"""
        result = ENumberParser.normalize_enumber("e13*1234*5678*00")
        assert result == "e13*1234*5678*00"

    def test_normalize_enumber_with_spaces(self):
        """Test normalization of E-number with spaces"""
        result = ENumberParser.normalize_enumber("e13 1234 5678 00")
        assert result == "e13*1234*5678*00"

    def test_normalize_enumber_with_hyphens(self):
        """Test normalization of E-number with hyphens"""
        result = ENumberParser.normalize_enumber("e13-1234-5678-00")
        assert result == "e13*1234*5678*00"

    def test_normalize_enumber_compact(self):
        """Test normalization of compact E-number"""
        result = ENumberParser.normalize_enumber("e131234567800")
        assert result == "e13*1234*5678*00"

    def test_normalize_enumber_padding(self):
        """Test normalization with zero padding"""
        result = ENumberParser.normalize_enumber("e1*234*567*8")
        assert result == "e01*0234*0567*08"

    def test_normalize_enumber_invalid(self):
        """Test normalization of invalid E-number"""
        result = ENumberParser.normalize_enumber("invalid")
        assert result is None

    def test_parse_enumber_components(self):
        """Test parsing E-number into components"""
        result = ENumberParser.parse_enumber("e13*1234*5678*00")
        assert result == (13, 1234, 5678, 0)

    def test_parse_enumber_invalid(self):
        """Test parsing invalid E-number"""
        result = ENumberParser.parse_enumber("invalid")
        assert result is None

    def test_is_enumber_positive(self):
        """Test E-number detection for valid E-numbers"""
        assert ENumberParser.is_enumber("e13*1234*5678*00") is True
        assert ENumberParser.is_enumber("This contains e13*1234*5678*00") is True

    def test_is_enumber_negative(self):
        """Test E-number detection for invalid text"""
        assert ENumberParser.is_enumber("not an enumber") is False
        assert ENumberParser.is_enumber("") is False

    def test_fuzzy_match_exact(self):
        """Test fuzzy matching with exact match"""
        query_enumbers = ["e13*1234*5678*00"]
        doc_enumbers = ["e13*1234*5678*00"]
        
        assert ENumberParser.fuzzy_match_enumbers(query_enumbers, doc_enumbers) is True

    def test_fuzzy_match_authority_base(self):
        """Test fuzzy matching with same authority and base"""
        query_enumbers = ["e13*1234*5678*00"]
        doc_enumbers = ["e13*1234*9999*99"]
        
        assert ENumberParser.fuzzy_match_enumbers(query_enumbers, doc_enumbers) is True

    def test_fuzzy_match_different(self):
        """Test fuzzy matching with different E-numbers"""
        query_enumbers = ["e13*1234*5678*00"]
        doc_enumbers = ["e14*1234*5678*00"]
        
        assert ENumberParser.fuzzy_match_enumbers(query_enumbers, doc_enumbers) is False

    def test_fuzzy_match_empty_lists(self):
        """Test fuzzy matching with empty lists"""
        assert ENumberParser.fuzzy_match_enumbers([], ["e13*1234*5678*00"]) is False
        assert ENumberParser.fuzzy_match_enumbers(["e13*1234*5678*00"], []) is False
        assert ENumberParser.fuzzy_match_enumbers([], []) is False

    def test_complex_text_extraction(self):
        """Test extraction from complex text"""
        text = """
        This is a homologation document for BMW X5.
        E-approval number: e13*1234*5678*00
        Additional approval: E13-9999-8888-77
        Also contains: e131111222233
        """
        enumbers = ENumberParser.extract_enumbers(text)
        
        assert len(enumbers) == 3
        assert "e13*1234*5678*00" in enumbers
        assert "e13*9999*8888*77" in enumbers
        assert "e13*1111*2222*33" in enumbers
