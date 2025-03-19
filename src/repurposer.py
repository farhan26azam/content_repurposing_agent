# repurposer.py

import logging
import time
from src.content_fetcher import ContentFetcher
from src.text_processor import TextProcessor
from src.gemini_handler import GeminiHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentRepurposer:
    """Orchestrates the content repurposing process."""
    
    def __init__(self, api_key=None):
        """
        Initialize the repurposer components.
        
        Args:
            api_key (str, optional): Gemini API key to use. If None, will try to load from environment.
        """
        self.fetcher = ContentFetcher()
        self.processor = TextProcessor()
        self.gemini = GeminiHandler(api_key=api_key)
    
    def repurpose(self, url, content_types, delay_between_calls=2, custom_instructions=None):
        """
        Repurpose content from a URL into specified formats.
        
        Args:
            url (str): URL to fetch content from
            content_types (list): List of content types to generate
            delay_between_calls (int): Delay in seconds between API calls
            custom_instructions (dict, optional): Dictionary of custom instructions for each content type
            
        Returns:
            dict: Dictionary of repurposed content by type
        """
        logger.info(f"Starting repurposing process for {url}")
        
        # Initialize custom instructions if not provided
        if custom_instructions is None:
            custom_instructions = {}
        
        # Step 1: Fetch content
        content_data = self.fetcher.fetch_content(url)
        # print("Fetched content in repurposer: ", content_data)
        if not content_data["content"]:
            return {"error": "Failed to fetch content from URL"}
        
        # Step 2: Process and chunk text
        chunks = self.processor.chunk_text(content_data["content"])
        
        # Step 3: Summarize each chunk
        logger.info("Summarizing chunks...")
        summarized_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            summary = self.gemini.chunk_summarize(chunk, content_data["title"])
            summarized_chunks.append(summary)
            # Add delay between chunk processing
            if i < len(chunks) - 1:
                time.sleep(delay_between_calls)
        
        # Step 4: Join summarized chunks
        condensed_content = self.processor.summarize_chunks(chunks, summarized_chunks)
        
        # Step 5: Generate repurposed content for each type
        results = {}
        for i, content_type in enumerate(content_types):
            logger.info(f"Generating {content_type} content")
            
            # Get custom instructions for this content type if available
            custom_instruction = custom_instructions.get(content_type, "")
            
            repurposed = self.gemini.create_repurposed_content(
                content_type, condensed_content, content_data["title"], custom_instruction
            )
            results[content_type] = repurposed
            
            # Add delay between content type generations (except for the last one)
            if i < len(content_types) - 1:
                time.sleep(delay_between_calls)
        
        return results
        
    def repurpose_from_text(self, title, content, content_types, delay_between_calls=2, custom_instructions=None):
        """
        Repurpose content from raw text into specified formats.
        
        Args:
            title (str): Title of the content
            content (str): Raw content text
            content_types (list): List of content types to generate
            delay_between_calls (int): Delay in seconds between API calls
            custom_instructions (dict, optional): Dictionary of custom instructions for each content type
            
        Returns:
            dict: Dictionary of repurposed content by type
        """
        logger.info(f"Starting repurposing process for content with title: {title}")
        
        # Initialize custom instructions if not provided
        if custom_instructions is None:
            custom_instructions = {}
        
        # Step 1: Process and chunk text
        chunks = self.processor.chunk_text(content)
        
        # Step 2: Summarize each chunk
        logger.info("Summarizing chunks...")
        summarized_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            summary = self.gemini.chunk_summarize(chunk, title)
            summarized_chunks.append(summary)
            # Add delay between chunk processing
            if i < len(chunks) - 1:
                time.sleep(delay_between_calls)
        
        # Step 3: Join summarized chunks
        condensed_content = self.processor.summarize_chunks(chunks, summarized_chunks)
        
        # Step 4: Generate repurposed content for each type
        results = {}
        for i, content_type in enumerate(content_types):
            logger.info(f"Generating {content_type} content")
            
            # Get custom instructions for this content type if available
            custom_instruction = custom_instructions.get(content_type, "")
            
            repurposed = self.gemini.create_repurposed_content(
                content_type, condensed_content, title, custom_instruction
            )
            results[content_type] = repurposed
            
            # Add delay between content type generations (except for the last one)
            if i < len(content_types) - 1:
                time.sleep(delay_between_calls)
        
        return results