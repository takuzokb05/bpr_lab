"""
State management for OCR processing
Handles progress.json for resumable processing
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class StateManager:
    """Manages processing state for resumable OCR"""
    
    def __init__(self, state_file: str = "progress.json"):
        """
        Initialize state manager
        
        Args:
            state_file: Path to state file (default: progress.json)
        """
        self.state_file = state_file
        self.state: Dict[str, Any] = {
            "last_processed_page": 0,
            "last_tail_text": "",
            "current_chapter": "",
            "total_pages": 0,
            "batch_size": 10,
            "overlap": 1
        }
        
    def load(self) -> bool:
        """
        Load state from file
        
        Returns:
            True if state loaded successfully, False otherwise
        """
        if not os.path.exists(self.state_file):
            return False
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)
                
            # Validate required fields
            required_fields = ["last_processed_page", "total_pages"]
            if not all(field in loaded_state for field in required_fields):
                print(f"⚠️ Warning: State file missing required fields. Starting fresh.")
                return False
                
            self.state.update(loaded_state)
            print(f"✓ Loaded state: Last processed page {self.state['last_processed_page']}/{self.state['total_pages']}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Warning: Could not load state file: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save state to file with atomic write
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Write to temporary file first
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            
            # Atomic rename
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            os.rename(temp_file, self.state_file)
            
            return True
            
        except IOError as e:
            print(f"❌ Error: Could not save state: {e}")
            return False
    
    def update(self, **kwargs) -> None:
        """
        Update state fields
        
        Args:
            **kwargs: Fields to update
        """
        self.state.update(kwargs)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get state value
        
        Args:
            key: State key
            default: Default value if key not found
        
        Returns:
            State value or default
        """
        return self.state.get(key, default)
    
    def should_resume(self) -> bool:
        """
        Check if processing should resume from saved state
        
        Returns:
            True if there's progress to resume from
        """
        return self.state["last_processed_page"] > 0 and self.state["total_pages"] > 0
    
    def get_next_batch(self) -> Optional[tuple]:
        """
        Calculate next batch to process
        
        Returns:
            Tuple of (input_start, input_end, output_start, output_end) or None if complete
        """
        last_page = self.state["last_processed_page"]
        total_pages = self.state["total_pages"]
        batch_size = self.state["batch_size"]
        overlap = self.state["overlap"]
        
        if last_page >= total_pages:
            return None
        
        # Output range
        output_start = last_page + 1
        output_end = min(output_start + batch_size - 1, total_pages)
        
        # Input range (with overlap)
        input_start = max(1, output_start - overlap)
        input_end = min(total_pages, output_end + overlap)
        
        return (input_start, input_end, output_start, output_end)
    
    def reset(self) -> None:
        """Reset state to initial values"""
        self.state = {
            "last_processed_page": 0,
            "last_tail_text": "",
            "current_chapter": "",
            "total_pages": 0,
            "batch_size": 10,
            "overlap": 1
        }
