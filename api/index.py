import streamlit as st
from streamlit.web import bootstrap
import sys
import os
import logging
import time
import re
import markdown
import json

# Ensure src is in the python path.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.repurposer import ContentRepurposer
from src.gemini_handler import GeminiHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_api_key(api_key):
    """Basic validation for Gemini API key format."""
    if not api_key or not isinstance(api_key, str):
        return False
    pattern = r'^[A-Za-z0-9_-]{39}$'
    return bool(re.match(pattern, api_key))

def main():
    st.set_page_config(
        page_title="Content Repurposer",
        page_icon="📝",
        layout="wide",
    )

    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False

    st.title("🔄 Content Repurposer")
    st.subheader("Transform your articles into multiple content formats")

    with st.expander("ℹ️ About this app", expanded=True):
        st.markdown("""
        This app helps you repurpose your long-form content into various formats:
        - LinkedIn posts
        - Twitter threads
        - Email newsletters
        - Thought leadership comments

        You can either enter the URL of your blog post/article or paste the content directly.
        Then select the content types you want to generate, and click 'Repurpose Content'.

        ### API Key Required
        This app uses the Gemini API to generate content. You'll need to provide your own API key.

        1.  Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2.  Enter it in the API Key field below
        3.  Your API key is stored only in your browser session and is not saved by this app
        """)

    st.subheader("🔑 API Key")

    api_key_col1, api_key_col2 = st.columns([3, 1])

    with api_key_col1:
        api_key = st.text_input(
            "Enter your Gemini API Key",
            type="password",
            value=st.session_state.api_key,
            help="Get your API key from Google AI Studio"
        )

    with api_key_col2:
        if st.button("Validate Key"):
            if is_valid_api_key(api_key):
                try:
                    test_handler = GeminiHandler(api_key=api_key)
                    st.session_state.api_key = api_key
                    st.session_state.api_key_valid = True
                    st.success("API key is valid!")
                except Exception as e:
                    st.error(f"Error validating API key: {str(e)}")
                    st.session_state.api_key_valid = False
            else:
                st.error("Invalid API key format")
                st.session_state.api_key_valid = False

    if st.session_state.api_key:
        if st.session_state.api_key_valid:
            st.success("API key is set and valid. You can now use the app.")
        else:
            st.warning("API key is set but not validated. Please click 'Validate Key'.")
    else:
        st.warning("Please enter your Gemini API key to use the app.")

    if st.session_state.api_key_valid:
        # Input section
        st.subheader("Input")

        # Create tabs for URL and manual input methods
        input_method = st.radio("Choose input method:", ["URL", "Paste Content"])

        url = ""
        pasted_content = ""
        article_title = ""

        if input_method == "URL":
            url = st.text_input("Enter the URL of your article or blog post:")
        else:
            article_title = st.text_input("Enter the title of your article:")
            pasted_content = st.text_area("Paste your article content here:", height=300)

        # Content type selection
        st.subheader("Select Content Types")

        # Dictionary to store custom instructions for each content type
        custom_instructions = {}

        # Create a container for content types
        content_types_container = st.container()

        with content_types_container:
            col1, col2 = st.columns(2)

            with col1:
                linkedin = st.checkbox("LinkedIn Post", value=True)
                if linkedin:
                    with st.expander("LinkedIn Post Instructions"):
                        custom_instructions["linkedin"] = st.text_area(
                            "Custom instructions for LinkedIn Post",
                            placeholder="E.g., Use more emojis, focus on leadership aspects, include a call-to-action at the end",
                            key="linkedin_instructions"
                        )

                twitter = st.checkbox("Twitter Thread", value=True)
                if twitter:
                    with st.expander("Twitter Thread Instructions"):
                        custom_instructions["twitter"] = st.text_area(
                            "Custom instructions for Twitter Thread",
                            placeholder="E.g., Include relevant hashtags, focus on data points, use more engaging language",
                            key="twitter_instructions"
                        )

            with col2:
                email = st.checkbox("Email Newsletter", value=True)
                if email:
                    with st.expander("Email Newsletter Instructions"):
                        custom_instructions["email"] = st.text_area(
                            "Custom instructions for Email Newsletter",
                            placeholder="E.g., Write in a professional tone, include a personal story, add bullet points for key takeaways",
                            key="email_instructions"
                        )

                thought_leadership = st.checkbox("Thought Leadership Comments", value=True)
                if thought_leadership:
                    with st.expander("Thought Leadership Instructions"):
                        custom_instructions["thought_leadership"] = st.text_area(
                            "Custom instructions for Thought Leadership Comments",
                            placeholder="E.g., Focus on industry trends, mention competing viewpoints, pose thought-provoking questions",
                            key="thought_leadership_instructions"
                        )

        # API configuration
        with st.expander("Advanced Settings"):
            delay_seconds = st.slider("Delay between API calls (seconds)", 1, 10, 3,
                                    help="Increase this value if you're hitting API rate limits")

        # Gather selected content types
        selected_types = []
        if linkedin:
            selected_types.append("linkedin")
        if twitter:
            selected_types.append("twitter")
        if email:
            selected_types.append("email")
        if thought_leadership:
            selected_types.append("thought_leadership")

        # Process button - Enable if either URL is provided or content is pasted
        button_disabled = (input_method == "URL" and not url) or \
            (input_method == "Paste Content" and (not pasted_content or not article_title)) or \
            not selected_types

        if st.button("Repurpose Content", disabled=button_disabled):
            if input_method == "URL" and not url:
                st.error("Please enter a URL")
            elif input_method == "Paste Content" and not pasted_content:
                st.error("Please paste article content")
            elif input_method == "Paste Content" and not article_title:
                st.error("Please enter an article title")
            elif not selected_types:
                st.error("Please select at least one content type")
            else:
                status_container = st.empty()
                progress_container = st.container()

                with status_container:
                    st.info("Process started. This may take a few minutes...")

                with progress_container:
                    progress_bar = st.progress(0)
                    progress_text = st.empty()

                    try:
                        # Initialize repurposer with user's API key
                        repurposer = ContentRepurposer(api_key=st.session_state.api_key)

                        # Content data dictionary to store title and content
                        content_data = {"title": "", "content": ""}

                        # Handle different input methods
                        if input_method == "URL":
                            # Show fetch content progress
                            progress_text.text("Fetching and analyzing content from URL...")
                            progress_bar.progress(10)

                            # Fetch content from URL
                            content_data = repurposer.fetcher.fetch_content(url)
                            if not content_data["content"]:
                                st.error("Access denied by the provider. Please try 'Paste Content' option or use a different URL.")
                                return

                            # Process with the repurpose method
                            progress_text.text("Processing content...")
                            progress_bar.progress(20)
                            results = repurposer.repurpose(url, selected_types, delay_seconds, custom_instructions)
                        else:
                            # For manually pasted content
                            progress_text.text("Processing pasted content...")
                            progress_bar.progress(10)

                            # Process with the repurpose_from_text method
                            results = repurposer.repurpose_from_text(
                                article_title,
                                pasted_content,
                                selected_types,
                                delay_seconds,
                                custom_instructions
                            )

                        # Complete progress
                        progress_bar.progress(100)
                        progress_text.text("All content generated successfully!")
                        time.sleep(1)

                        # Clear progress indicators
                        progress_text.empty()
                        progress_bar.empty()

                        # Update status
                        status_container.success("Content repurposed successfully!")

                        # Create tabs for each content type
                        tabs = st.tabs([content_type.capitalize() for content_type in selected_types])

                        for i, content_type in enumerate(selected_types):
                            with tabs[i]:
                                st.markdown("### " + content_type.capitalize() + " Content")

                                # Display the content with markdown rendering
                                st.markdown(results[content_type])

                                # Also provide a raw text area for copying
                                with st.expander("Show copyable version"):
                                    st.text_area(
                                        "Raw Content",
                                        value=results[content_type],
                                        height=400
                                    )

                                st.download_button(
                                    label=f"Download {content_type.capitalize()} Content",
                                    data=results[content_type],
                                    file_name=f"{content_type}_content.txt",
                                    mime="text/plain"
                                )

                    except Exception as e:
                        status_container.error(f"An error occurred: {str(e)}")
                        logger.error(f"Error in repurposing process: {e}", exc_info=True)
                        progress_text.text(f"Error: {str(e)}")

                        # Show error details and suggestions
                        if "429" in str(e):
                            st.error("""
                            You've hit API rate limits. Try these solutions:
                            1.  Increase the delay between API calls in Advanced Settings
                            2.  Generate fewer content types at once
                            3.  Try again later when your quota resets
                            """)
                        elif "403" in str(e) or "401" in str(e):
                            st.error("API key error. Please check your Gemini API key and try validating it again.")
                        else:
                            st.error("An unknown error occurred. Please check the logs for details.")
    else:
        # Show a placeholder when API key is not valid
        st.info("Please enter and validate your API key to use the app.")

def handler(event, context):
    """Vercel handler function."""
    try:
        return bootstrap.run(main,"", {})
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }