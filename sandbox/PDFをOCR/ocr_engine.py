"""
OCR Engine - Gemini API integration for OCR processing
"""

import os
from typing import List, Optional, Tuple
import google.generativeai as genai
from PIL import Image

from prompts import build_prompt, extract_chapter_from_text, extract_last_lines
from error_handler import with_retry, APIError


class OCREngine:
    """Handles OCR processing using Gemini API"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash", 
                 fallback_model: str = "gemini-3-pro", timeout: int = 60):
        """
        Initialize OCR engine
        
        Args:
            api_key: Google API key
            model_name: Primary model name (default: gemini-3-flash)
            fallback_model: Fallback model for complex pages
            timeout: API timeout in seconds
        """
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.timeout = timeout
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(model_name)
        self.fallback = genai.GenerativeModel(fallback_model) if fallback_model else None
        
        print(f"✓ Initialized OCR engine with {model_name}")
    
    @with_retry(max_retries=3)
    def process_batch(self, image_paths: List[str], output_start: int, output_end: int,
                     last_tail_text: str = "", current_chapter: str = "",
                     use_fallback: bool = False) -> str:
        """
        Process a batch of pages with OCR
        
        Args:
            image_paths: List of paths to page images
            output_start: First page to output
            output_end: Last page to output
            last_tail_text: Last 3 lines from previous batch
            current_chapter: Current chapter name
            use_fallback: Use fallback model instead of primary
        
        Returns:
            Markdown text for the batch
        
        Raises:
            APIError: If API call fails
        """
        # Calculate input range
        input_start = output_start - (len(image_paths) - (output_end - output_start + 1)) // 2
        input_end = input_start + len(image_paths) - 1
        
        # Build prompt
        prompt = build_prompt(
            start_page=input_start,
            end_page=input_end,
            output_start=output_start,
            output_end=output_end,
            last_tail_text=last_tail_text,
            current_chapter=current_chapter
        )
        
        # Load images
        images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                images.append(img)
            except Exception as e:
                raise APIError(f"Failed to load image {path}: {e}")
        
        # Select model
        model = self.fallback if (use_fallback and self.fallback) else self.model
        model_name = self.fallback_model if use_fallback else self.model_name
        
        print(f"  Processing pages {output_start}-{output_end} with {model_name}...")
        
        try:
            # Create content with prompt and images
            content = [prompt] + images
            
            # Generate response
            response = model.generate_content(
                content,
                request_options={"timeout": self.timeout}
            )
            
            # Extract text
            if not response.text:
                raise APIError("Empty response from API")
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific errors
            if "rate limit" in error_msg.lower():
                raise APIError(f"Rate limit exceeded: {e}")
            elif "quota" in error_msg.lower():
                raise APIError(f"Quota exceeded: {e}")
            elif "invalid" in error_msg.lower():
                raise APIError(f"Invalid API key or request: {e}")
            else:
                raise APIError(f"API error: {e}")
    
    def extract_metadata(self, markdown_text: str) -> Tuple[str, str]:
        """
        Extract metadata from processed text
        
        Args:
            markdown_text: Processed markdown text
        
        Returns:
            Tuple of (last_tail_text, current_chapter)
        """
        # Extract last 3 lines for continuity
        last_tail = extract_last_lines(markdown_text, num_lines=3)
        
        # Extract chapter if present
        chapter = extract_chapter_from_text(markdown_text)
        
        return (last_tail, chapter)
    
    def test_connection(self) -> bool:
        """
        Test API connection with a simple request
        
        Returns:
            True if connection successful
        """
        try:
            response = self.model.generate_content("Hello")
            return bool(response.text)
        except Exception as e:
            print(f"❌ API connection test failed: {e}")
            return False


def load_api_key(key_file: str = "API_KEY.txt") -> str:
    """
    Load API key from file
    
    Args:
        key_file: Path to API key file
    
    Returns:
        API key string
    
    Raises:
        FileNotFoundError: If key file not found
        ValueError: If key file is invalid
    """
    if not os.path.exists(key_file):
        raise FileNotFoundError(
            f"API key file not found: {key_file}\n"
            "Please create API_KEY.txt with your Google API key."
        )
    
    try:
        with open(key_file, 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
        
        if not api_key or len(api_key) < 20:
            raise ValueError("Invalid API key format")
        
        return api_key
        
    except Exception as e:
        raise ValueError(f"Failed to load API key: {e}")
