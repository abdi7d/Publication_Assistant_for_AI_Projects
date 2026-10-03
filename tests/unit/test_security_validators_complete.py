"""
Comprehensive security validator tests for 100% coverage
Tests all paths in file_validators.py, input_validators.py, and validators.py
"""

import pytest
from security.validators.file_validators import (
    sanitize_filename, validate_extension, validate_mime_type,
    validate_upload_size, validate_upload
)
from security.validators.input_validators import validate_prompt
from security.validators.validators import (
    sanitize_text, validate_prompt_length, has_suspicious_chars,
    validate_prompt_tokens, simple_token_estimate
)


class TestFileValidators:
    """Complete tests for file_validators.py"""
    
    def test_sanitize_filename_valid(self):
        """Test sanitize_filename with valid filename"""
        result = sanitize_filename("document.pdf")
        assert "document" in result
    
    def test_sanitize_filename_with_path(self):
        """Test sanitize_filename removes path separators"""
        result = sanitize_filename("../etc/passwd.txt")
        assert "/" not in result and "\\" not in result
    
    def test_sanitize_filename_special_chars(self):
        """Test sanitize_filename removes special characters"""
        result = sanitize_filename("file@#$%.pdf")
        assert "@" not in result and "#" not in result
    
    def test_sanitize_filename_unicode(self):
        """Test sanitize_filename handles unicode"""
        result = sanitize_filename("文档.pdf")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_sanitize_filename_null_byte(self):
        """Test sanitize_filename removes null bytes"""
        result = sanitize_filename("file\x00.pdf")
        assert "\x00" not in result
    
    def test_sanitize_filename_none(self):
        """Test sanitize_filename with None"""
        result = sanitize_filename(None)
        assert isinstance(result, str)
    
    def test_sanitize_filename_empty(self):
        """Test sanitize_filename with empty string"""
        result = sanitize_filename("")
        assert isinstance(result, str)
    
    def test_validate_extension_pdf(self):
        """Test validate_extension with valid .pdf"""
        ok, msg = validate_extension("document.pdf")
        assert ok is True
        assert msg == "ok"
    
    def test_validate_extension_txt(self):
        """Test validate_extension with valid .txt"""
        ok, msg = validate_extension("notes.txt")
        assert ok is True
    
    def test_validate_extension_md(self):
        """Test validate_extension with valid .md"""
        ok, msg = validate_extension("README.md")
        assert ok is True
    
    def test_validate_extension_jpg(self):
        """Test validate_extension with valid .jpg"""
        ok, msg = validate_extension("image.jpg")
        assert ok is True
    
    def test_validate_extension_jpeg(self):
        """Test validate_extension with valid .jpeg"""
        ok, msg = validate_extension("photo.jpeg")
        assert ok is True
    
    def test_validate_extension_png(self):
        """Test validate_extension with valid .png"""
        ok, msg = validate_extension("screenshot.png")
        assert ok is True
    
    def test_validate_extension_docx(self):
        """Test validate_extension with valid .docx"""
        ok, msg = validate_extension("document.docx")
        assert ok is True
    
    def test_validate_extension_invalid_exe(self):
        """Test validate_extension rejects .exe"""
        ok, msg = validate_extension("script.exe")
        assert ok is False
        assert msg == "extension_not_allowed"
    
    def test_validate_extension_invalid_bat(self):
        """Test validate_extension rejects .bat"""
        ok, msg = validate_extension("script.bat")
        assert ok is False
    
    def test_validate_extension_double_extension(self):
        """Test validate_extension with double extension (e.g., .pdf.exe)"""
        ok, msg = validate_extension("document.pdf.exe")
        assert ok is False  # Should only check last extension
    
    def test_validate_extension_no_extension(self):
        """Test validate_extension with no extension"""
        ok, msg = validate_extension("filename")
        assert ok is False
        assert msg == "no_extension"
    
    def test_validate_extension_case_insensitive(self):
        """Test validate_extension is case-insensitive"""
        ok, msg = validate_extension("document.PDF")
        assert ok is True
        
        ok, msg = validate_extension("document.Pdf")
        assert ok is True
    
    def test_validate_extension_hidden_file(self):
        """Test validate_extension with hidden file"""
        ok, msg = validate_extension(".hidden.pdf")
        assert ok is True
    
    def test_validate_mime_type_pdf(self):
        """Test validate_mime_type with PDF"""
        ok, msg = validate_mime_type(b"PDF", "document.pdf")
        assert isinstance(ok, bool)
    
    def test_validate_mime_type_text(self):
        """Test validate_mime_type with text"""
        ok, msg = validate_mime_type(b"text", "notes.txt")
        assert isinstance(ok, bool)
    
    def test_validate_mime_type_image(self):
        """Test validate_mime_type with image"""
        ok, msg = validate_mime_type(b"image", "photo.jpg")
        assert isinstance(ok, bool)
    
    def test_validate_mime_type_unknown_extension(self):
        """Test validate_mime_type with unknown extension"""
        ok, msg = validate_mime_type(b"data", "file.xyz")
        assert ok is False
    
    def test_validate_upload_size_valid(self):
        """Test validate_upload_size with valid size"""
        ok, msg = validate_upload_size(b"x" * 1000)
        assert ok is True
        assert msg == "ok"
    
    def test_validate_upload_size_oversized(self):
        """Test validate_upload_size with oversized file"""
        # Create file larger than max (typically 50MB)
        large_data = b"x" * (60 * 1024 * 1024)
        ok, msg = validate_upload_size(large_data)
        assert ok is False
        assert msg == "file_too_large"
    
    def test_validate_upload_valid(self):
        """Test validate_upload with valid file"""
        ok, msg = validate_upload(b"PDF", "document.pdf", "application/pdf")
        assert ok is True
    
    def test_validate_upload_invalid_extension(self):
        """Test validate_upload rejects invalid extension"""
        ok, msg = validate_upload(b"EXE", "script.exe", "application/x-msdownload")
        assert ok is False
    
    def test_validate_upload_invalid_mime(self):
        """Test validate_upload rejects invalid MIME"""
        ok, msg = validate_upload(b"x", "file.pdf", "application/x-executable")
        assert ok is False
        assert msg == "mime_type_not_allowed"
    
    def test_validate_upload_no_mime(self):
        """Test validate_upload with no MIME specified"""
        ok, msg = validate_upload(b"data", "document.pdf", None)
        assert ok is True


class TestInputValidators:
    """Complete tests for input_validators.py"""
    
    def test_validate_prompt_valid(self):
        """Test validate_prompt with valid prompt"""
        ok, msg = validate_prompt("This is a valid prompt")
        assert ok is True
        assert msg == ""
    
    def test_validate_prompt_empty(self):
        """Test validate_prompt rejects empty prompt"""
        ok, msg = validate_prompt("")
        assert ok is False
    
    def test_validate_prompt_whitespace_only(self):
        """Test validate_prompt rejects whitespace-only prompt"""
        ok, msg = validate_prompt("   ")
        assert ok is False
    
    def test_validate_prompt_null_byte(self):
        """Test validate_prompt detects null bytes"""
        ok, msg = validate_prompt("Normal text\x00injected")
        assert ok is False
    
    def test_validate_prompt_control_chars(self):
        """Test validate_prompt detects control characters"""
        ok, msg = validate_prompt("Text with \x01 control char")
        assert ok is False
    
    def test_validate_prompt_very_long(self):
        """Test validate_prompt rejects very long prompt"""
        long_prompt = "a" * 100000
        ok, msg = validate_prompt(long_prompt)
        assert ok is False
    
    def test_validate_prompt_unicode(self):
        """Test validate_prompt handles unicode"""
        ok, msg = validate_prompt("Café with naïve résumé")
        assert ok is True


class TestGeneralValidators:
    """Complete tests for validators.py"""
    
    def test_sanitize_text_normal(self):
        """Test sanitize_text with normal input"""
        result = sanitize_text("Normal text")
        assert result == "Normal text"
    
    def test_sanitize_text_extra_spaces(self):
        """Test sanitize_text normalizes spaces"""
        result = sanitize_text("Text  with   extra    spaces")
        assert "   " not in result
    
    def test_sanitize_text_leading_trailing_spaces(self):
        """Test sanitize_text removes leading/trailing spaces"""
        result = sanitize_text("  text  ")
        assert result == "text"
    
    def test_sanitize_text_newlines(self):
        """Test sanitize_text handles newlines"""
        result = sanitize_text("Line1\n\nLine2")
        assert isinstance(result, str)
    
    def test_sanitize_text_control_chars(self):
        """Test sanitize_text removes control characters"""
        result = sanitize_text("Text\x00with\x01control")
        assert "\x00" not in result
        assert "\x01" not in result
    
    def test_sanitize_text_none(self):
        """Test sanitize_text handles None"""
        result = sanitize_text(None)
        assert result == ""
    
    def test_sanitize_text_tabs(self):
        """Test sanitize_text normalizes tabs"""
        result = sanitize_text("Text\t\twith\ttabs")
        assert "\t" not in result
    
    def test_validate_prompt_length_valid(self):
        """Test validate_prompt_length with valid length"""
        ok, msg = validate_prompt_length("This is valid text")
        assert ok is True
        assert msg == "ok"
    
    def test_validate_prompt_length_empty(self):
        """Test validate_prompt_length rejects empty"""
        ok, msg = validate_prompt_length("")
        assert ok is False
        assert msg == "empty_prompt"
    
    def test_validate_prompt_length_whitespace_only(self):
        """Test validate_prompt_length rejects whitespace"""
        ok, msg = validate_prompt_length("   ")
        assert ok is False
    
    def test_validate_prompt_length_too_long(self):
        """Test validate_prompt_length rejects too long"""
        long_text = "a" * 21000
        ok, msg = validate_prompt_length(long_text)
        assert ok is False
        assert msg == "prompt_too_large"
    
    def test_has_suspicious_chars_clean(self):
        """Test has_suspicious_chars with clean text"""
        result = has_suspicious_chars("Normal text 123")
        assert result is False
    
    def test_has_suspicious_chars_null_byte(self):
        """Test has_suspicious_chars detects null byte"""
        result = has_suspicious_chars("Text\x00with")
        assert result is True
    
    def test_has_suspicious_chars_control(self):
        """Test has_suspicious_chars detects control char"""
        result = has_suspicious_chars("Text\x01with")
        assert result is True
    
    def test_has_suspicious_chars_delete(self):
        """Test has_suspicious_chars detects DEL char"""
        result = has_suspicious_chars("Text\x7fwith")
        assert result is True
    
    def test_has_suspicious_chars_none(self):
        """Test has_suspicious_chars handles None"""
        result = has_suspicious_chars(None)
        assert result is False
    
    def test_simple_token_estimate(self):
        """Test simple_token_estimate"""
        estimate = simple_token_estimate("This is a test")
        assert estimate > 0
        assert isinstance(estimate, int)
    
    def test_simple_token_estimate_empty(self):
        """Test simple_token_estimate with empty"""
        estimate = simple_token_estimate("")
        assert estimate >= 1  # Should return at least 1
    
    def test_simple_token_estimate_none(self):
        """Test simple_token_estimate with None"""
        estimate = simple_token_estimate(None)
        assert estimate >= 1
    
    def test_validate_prompt_tokens_valid(self):
        """Test validate_prompt_tokens with valid"""
        ok, msg = validate_prompt_tokens("a" * 100)
        assert ok is True
        assert msg == "ok"
    
    def test_validate_prompt_tokens_too_many(self):
        """Test validate_prompt_tokens exceeds limit"""
        # Create text with > 5000 tokens (roughly 20K chars)
        ok, msg = validate_prompt_tokens("a" * 25000)
        assert ok is False
        assert msg == "tokens_exceed_limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
