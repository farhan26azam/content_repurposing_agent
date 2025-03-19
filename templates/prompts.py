"""
Prompt templates for content repurposing.
These templates define how to instruct the AI to transform content into different formats.
"""

# Template for condensing/summarizing chunks
CHUNK_SUMMARIZATION_TEMPLATE = """
You are processing a section of an article titled "{title}". 
Summarize this section while preserving all key information, facts, and insights.
Keep the most important quotes and statistics intact.
Maintain the tone and style of the original content.

SECTION:
{chunk}

SUMMARIZED SECTION:
"""

# Template for LinkedIn posts
LINKEDIN_POST_TEMPLATE = """
Create a LinkedIn post based on this article titled "{title}".
Include:
1. A compelling hook that grabs attention in the first line
2. Structured/numbered key insights from the article (enough detail to be understandable and compelling)
3. A thought-provoking question or call-to-action at the end
4. 1-5 relevant hashtags

Format with appropriate line breaks and emojis where relevant.
Keep under 3,000 characters and make it feel professional but conversational.

ARTICLE CONTENT:
{content}

LINKEDIN POST:
"""

# Template for Twitter threads
TWITTER_THREAD_TEMPLATE = """
Create a Twitter thread (generally between 5-7 tweets) based on this article titled "{title}".
First tweet should have a powerful hook that makes people want to read the thread.
Each subsequent tweet should cover a key point with engaging language.
Final tweet should include a thought-provoking question or call-to-action.
Include 2-5 relevant hashtags in the final tweet.
Each tweet should be concise but still have enough information to be compelling, maintain the balance.
Number each tweet (1/7, 2/7, etc.) to make it clear it's a thread.

ARTICLE CONTENT:
{content}

TWITTER THREAD:
"""

# Template for email newsletters
EMAIL_NEWSLETTER_TEMPLATE = """
Create an email newsletter based on this article titled "{title}".
Include:
1. An engaging subject line (marked with "SUBJECT:")
2. A personal-feeling introduction that hooks the reader
3. 3-5 key insights (can be more depending on the content) from the article with brief explanations
4. Bullet points for easy scanning
5. A practical takeaway or application for the reader
6. A clear call-to-action

Format it professionally with appropriate sections and make it conversational.
Use subheadings where appropriate.

ARTICLE CONTENT:
{content}

EMAIL NEWSLETTER:
"""

# Template for thought leadership comments
THOUGHT_LEADERSHIP_TEMPLATE = """
Create 3 thought leadership comments that could be used on social media or forums
based on this article titled "{title}".

Each comment should:
1. Show expertise and unique insight
2. Reference the article content but add new perspective or extend the ideas
3. Be 2-3 paragraphs long
4. End with an open-ended question to encourage discussion
5. Be written in a professional but conversational tone

Label each comment as "COMMENT 1:", "COMMENT 2:", and "COMMENT 3:"

ARTICLE CONTENT:
{content}

THOUGHT LEADERSHIP COMMENTS:
"""

# Dictionary mapping content types to their templates
TEMPLATES = {
    "chunk_summarization": CHUNK_SUMMARIZATION_TEMPLATE,
    "linkedin": LINKEDIN_POST_TEMPLATE,
    "twitter": TWITTER_THREAD_TEMPLATE,
    "email": EMAIL_NEWSLETTER_TEMPLATE,
    "thought_leadership": THOUGHT_LEADERSHIP_TEMPLATE
}

def get_template(template_type):
    """
    Get a prompt template by type.
    
    Args:
        template_type (str): The type of template to retrieve
        
    Returns:
        str: The prompt template
    """
    return TEMPLATES.get(template_type, "")