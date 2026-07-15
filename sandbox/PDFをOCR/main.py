"""
Main orchestrator for PDF OCR processing
"""

import argparse
import sys
import yaml
from pathlib import Path
from tqdm import tqdm

from pdf_processor import PDFProcessor
from ocr_engine import OCREngine, load_api_key
from state_manager import StateManager
from error_handler import ErrorHandler, OCRError


def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ Warning: Could not load config file: {e}")
        print("Using default configuration...")
        return {
            "api": {
                "model": "gemini-3-flash",
                "fallback_model": "gemini-3-pro",
                "max_retries": 3,
                "timeout": 60
            },
            "processing": {
                "batch_size": 10,
                "overlap": 1,
                "dpi": 300,
                "image_format": "png"
            },
            "output": {
                "markdown_file": "output.md",
                "log_dir": "logs",
                "temp_dir": "temp_pages"
            }
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PDF OCR with Gemini API - Stateful Sliding Window System"
    )
    parser.add_argument("--input", "-i", type=str, help="Input PDF file")
    parser.add_argument("--resume", "-r", action="store_true", help="Resume from saved state")
    parser.add_argument("--batch-size", "-b", type=int, help="Pages per batch (default: 10)")
    parser.add_argument("--model", "-m", type=str, help="Model name (default: gemini-3-flash)")
    parser.add_argument("--force", "-f", action="store_true", help="Force reconvert PDF")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temp files and exit")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override config with command line arguments
    if args.batch_size:
        config["processing"]["batch_size"] = args.batch_size
    if args.model:
        config["api"]["model"] = args.model
    
    # Initialize components
    pdf_processor = PDFProcessor(
        output_dir=config["output"]["temp_dir"],
        dpi=config["processing"]["dpi"],
        image_format=config["processing"]["image_format"]
    )
    
    state_manager = StateManager()
    error_handler = ErrorHandler(
        max_retries=config["api"]["max_retries"],
        log_dir=config["output"]["log_dir"]
    )
    
    # Handle cleanup
    if args.cleanup:
        pdf_processor.cleanup()
        if Path("progress.json").exists():
            Path("progress.json").unlink()
            print("✓ Removed progress.json")
        return
    
    # Check for resume
    if args.resume:
        if not state_manager.load():
            print("❌ No saved state found. Please specify --input to start new processing.")
            sys.exit(1)
        print("✓ Resuming from saved state...")
    else:
        if not args.input:
            print("❌ Error: Please specify --input <pdf_file> or --resume")
            parser.print_help()
            sys.exit(1)
        
        # Convert PDF to images
        try:
            total_pages = pdf_processor.convert_pdf(args.input, force=args.force)
        except Exception as e:
            print(f"❌ Error converting PDF: {e}")
            sys.exit(1)
        
        # Initialize state
        state_manager.update(
            total_pages=total_pages,
            batch_size=config["processing"]["batch_size"],
            overlap=config["processing"]["overlap"]
        )
        state_manager.save()
    
    # Load API key and initialize OCR engine
    try:
        api_key = load_api_key()
        ocr_engine = OCREngine(
            api_key=api_key,
            model_name=config["api"]["model"],
            fallback_model=config["api"]["fallback_model"],
            timeout=config["api"]["timeout"]
        )
        
        # Test connection
        if not ocr_engine.test_connection():
            print("❌ API connection test failed. Please check your API key.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error initializing OCR engine: {e}")
        sys.exit(1)
    
    # Validate page images
    total_pages = state_manager.get("total_pages")
    valid, missing = pdf_processor.validate_pages(total_pages)
    if not valid:
        print(f"❌ Missing page images: {missing}")
        print("Run without --resume to reconvert PDF")
        sys.exit(1)
    
    # Open output file
    output_file = config["output"]["markdown_file"]
    mode = "a" if args.resume else "w"
    
    print(f"\n{'='*60}")
    print(f"Starting OCR Processing")
    print(f"{'='*60}")
    print(f"Total pages: {total_pages}")
    print(f"Batch size: {config['processing']['batch_size']}")
    print(f"Model: {config['api']['model']}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
    
    # Process batches
    try:
        with open(output_file, mode, encoding='utf-8') as f:
            # Progress bar
            pbar = tqdm(
                total=total_pages,
                initial=state_manager.get("last_processed_page"),
                desc="Processing",
                unit="page"
            )
            
            while True:
                # Get next batch
                batch_info = state_manager.get_next_batch()
                if not batch_info:
                    break
                
                input_start, input_end, output_start, output_end = batch_info
                
                # Get page images
                try:
                    image_paths = pdf_processor.get_page_paths(input_start, input_end)
                except Exception as e:
                    error_handler.log_error(output_start, e)
                    raise
                
                # Process batch
                try:
                    markdown_text = ocr_engine.process_batch(
                        image_paths=image_paths,
                        output_start=output_start,
                        output_end=output_end,
                        last_tail_text=state_manager.get("last_tail_text", ""),
                        current_chapter=state_manager.get("current_chapter", "")
                    )
                    
                    # Write to output
                    f.write(markdown_text)
                    f.write("\n\n")
                    f.flush()
                    
                    # Extract metadata
                    last_tail, chapter = ocr_engine.extract_metadata(markdown_text)
                    
                    # Update state
                    state_manager.update(
                        last_processed_page=output_end,
                        last_tail_text=last_tail,
                        current_chapter=chapter or state_manager.get("current_chapter", "")
                    )
                    state_manager.save()
                    
                    # Update progress bar
                    pbar.update(output_end - output_start + 1)
                    
                except OCRError as e:
                    error_handler.handle_api_error(e, output_start)
                    pbar.close()
                    sys.exit(1)
            
            pbar.close()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Processing interrupted by user")
        print(f"Progress saved. Resume with: python main.py --resume")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        error_handler.log_error(state_manager.get("last_processed_page", 0), e)
        sys.exit(1)
    
    # Success
    print(f"\n{'='*60}")
    print(f"✓ Processing complete!")
    print(f"{'='*60}")
    print(f"Output: {output_file}")
    print(f"Total pages: {total_pages}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
