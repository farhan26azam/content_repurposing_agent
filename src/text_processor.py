# text_processor.py

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Processes text content into manageable chunks and formats."""
    
    @staticmethod
    def clean_text(text):
        """
        Cleans text by removing extra whitespace and normalizing line breaks.
        
        Args:
            text (str): The text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    @staticmethod
    def chunk_text(text, max_tokens=4000):
        """
        Splits text into chunks respecting paragraph boundaries.
        
        Args:
            text (str): The text to chunk
            max_tokens (int): Approximate maximum number of tokens per chunk
                              (using a simple heuristic of ~4 chars per token)
            
        Returns:
            list: List of text chunks
        """
        # Clean the text first
        text = TextProcessor.clean_text(text)
        
        # Split by paragraphs
        paragraphs = re.split(r'\n\n+', text)
        
        chunks = []
        current_chunk = ""
        current_token_count = 0
        
        for paragraph in paragraphs:
            # Estimate token count (rough heuristic: ~4 chars per token)
            paragraph_tokens = len(paragraph) / 4
            
            if current_token_count + paragraph_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
                current_token_count = paragraph_tokens
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_token_count += paragraph_tokens
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Split content into {len(chunks)} chunks")
        return chunks
    
    @staticmethod
    def summarize_chunks(chunks, model_output):
        """
        Joins summarized chunks into a coherent text.
        
        Args:
            chunks (list): List of original chunks
            model_output (list): List of summarized chunks
            
        Returns:
            str: Joined, summarized content
        """
        if len(chunks) != len(model_output):
            logger.warning(f"Mismatch in chunk count: {len(chunks)} vs {len(model_output)}")
        
        result = "\n\n".join(model_output)
        return result