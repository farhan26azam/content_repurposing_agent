# #gemini_handler.py


import google.generativeai as genai
import os
import logging
import time
import random
from dotenv import load_dotenv
from templates.prompts import get_template

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiHandler:
    """Handles communication with Gemini API with retry logic."""
    
    def __init__(self, api_key=None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key (str, optional): Gemini API key. If None, will try to load from environment.
        """
        # Use provided API key or try to get from environment
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
            
        if not self.api_key:
            raise ValueError("No Gemini API key provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("Gemini API initialized")
    
    def _call_with_retry(self, prompt, max_retries=5, base_delay=2):
        """
        Call Gemini API with exponential backoff retry logic.
        
        Args:
            prompt (str): The prompt to send to Gemini
            max_retries (int): Maximum number of retry attempts
            base_delay (int): Base delay in seconds for backoff
            
        Returns:
            str: Model response text
        """
        retries = 0
        while retries <= max_retries:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) and retries < max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = (base_delay ** retries) + random.uniform(0, 1)
                    logger.warning(f"Rate limit hit, retrying in {delay:.2f} seconds (attempt {retries+1}/{max_retries})")
                    time.sleep(delay)
                    retries += 1
                else:
                    # For non-rate limiting errors or if we've run out of retries
                    logger.error(f"API error: {e}")
                    raise
    
    def chunk_summarize(self, chunk, original_title):
        """
        Summarize a chunk of text while preserving key information.
        
        Args:
            chunk (str): Text chunk to summarize
            original_title (str): Original content title for context
            
        Returns:
            str: Summarized text
        """
        # Try to get template, fallback to hardcoded template if not found
        try:
            prompt = get_template("chunk_summarization").format(
                title=original_title,
                chunk=chunk
            )
        except Exception as e:
            logger.warning(f"Template not found, using fallback: {e}")
            prompt = f"""
            Summarize the following chunk of content from an article titled "{original_title}".
            Preserve key information, quotes, statistics, and unique insights.
            Maintain the original tone and style.
            
            CHUNK:
            {chunk}
            
            SUMMARY:
            """
        
        try:
            return self._call_with_retry(prompt)
        except Exception as e:
            logger.error(f"Error in chunk summarization: {e}")
            return chunk
    
    def create_repurposed_content(self, content_type, condensed_content, original_title, custom_instruction=""):
        """
        Generate repurposed content based on the content type.
        
        Args:
            content_type (str): Type of content to generate (linkedin, twitter, etc.)
            condensed_content (str): Condensed article content
            original_title (str): Original content title
            custom_instruction (str, optional): Custom user instructions for content generation
            
        Returns:
            str: Repurposed content
        """
        # Define fallback prompts for each content type
        fallback_prompts = {
            "linkedin": f"""
            Create a LinkedIn post based on this article titled "{original_title}".
            Include a compelling hook, 3-4 key insights, and a thought-provoking question or call-to-action.
            Format with appropriate line breaks and emojis where relevant.
            Keep under 3,000 characters and make it feel professional but conversational.
            
            {"!IMPORTANT INSTRUCTIONS (if above instructions are conflicting, prioritize these): " + custom_instruction if custom_instruction else ""}
            
            ARTICLE CONTENT:
            {condensed_content}
            
            LINKEDIN POST:
            """,
            
            "twitter": f"""
            Create a Twitter thread (5-7 tweets) based on this article titled "{original_title}".
            First tweet should have a powerful hook.
            Each subsequent tweet should cover a key point with engaging language.
            Final tweet should include a thought-provoking question or call-to-action.
            Include relevant hashtags in the final tweet.
            Each tweet should be under 280 characters.
            
            {"!IMPORTANT INSTRUCTIONS (if above instructions are conflicting, prioritize these): " + custom_instruction if custom_instruction else ""}
            
            ARTICLE CONTENT:
            {condensed_content}
            
            TWITTER THREAD:
            """,
            
            "email": f"""
            Create an email newsletter based on this article titled "{original_title}".
            Include:
            1. An engaging subject line
            2. A personal-feeling introduction
            3. 3-5 key insights from the article with brief explanations
            4. A practical takeaway or application for the reader
            5. A call-to-action
            
            Format it professionally with appropriate sections and make it conversational.
            
            {"!IMPORTANT INSTRUCTIONS (if above instructions are conflicting, prioritize these): " + custom_instruction if custom_instruction else ""}
            
            ARTICLE CONTENT:
            {condensed_content}
            
            EMAIL NEWSLETTER:
            """,
            
            "thought_leadership": f"""
            Create 3 thought leadership comments that could be used on social media or forums
            based on this article titled "{original_title}".
            
            Each comment should:
            1. Show expertise and unique insight
            2. Reference the article content but add new perspective
            3. Be 2-3 paragraphs long
            4. End with an open-ended question to encourage discussion
            
            {"!IMPORTANT INSTRUCTIONS (if above instructions are conflicting, prioritize these): " + custom_instruction if custom_instruction else ""}
            
            ARTICLE CONTENT:
            {condensed_content}
            
            THOUGHT LEADERSHIP COMMENTS:
            """
        }
        
        # Try to get template, fallback to hardcoded template if not found
        try:
            # Get the template
            template = get_template(content_type)
            
            # Add custom instruction if provided
            if custom_instruction:
                # Add custom instruction before the content
                template_parts = template.split("ARTICLE CONTENT:")
                if len(template_parts) > 1:
                    template = f"{template_parts[0]}\n!IMPORTANT INSTRUCTIONS (if above instructions are conflicting, prioritize these): {custom_instruction}\n\nARTICLE CONTENT:{template_parts[1]}"
                else:
                    # If template format is different, append custom instruction at the end
                    template = f"{template}\n\n{custom_instruction}"
            
            prompt = template.format(
                title=original_title,
                content=condensed_content
            )
            
            # If template returns None or empty string, use fallback
            if not prompt and content_type in fallback_prompts:
                logger.warning(f"Empty template for {content_type}, using fallback")
                prompt = fallback_prompts[content_type]
        except Exception as e:
            logger.warning(f"Template not found for {content_type}, using fallback: {e}")
            if content_type in fallback_prompts:
                prompt = fallback_prompts[content_type]
            else:
                return f"Invalid content type: {content_type}"
        
        try:    
            return self._call_with_retry(prompt)
        except Exception as e:
            logger.error(f"Error generating {content_type} content after retries: {e}")
            return f"Error generating {content_type} content. Please try again later."