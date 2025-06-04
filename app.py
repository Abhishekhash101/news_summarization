import streamlit as st
import requests
from newspaper import Article
from transformers import pipeline

API_KEY = "8b049a034ec94ca1a58bad5d04ac6d4b" 

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

def get_news_links(query, api_key, num_results=5):
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': num_results,
        'apiKey': api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            st.error(f"API Error: {data.get('message')}")
            return []
        return [{'title': article['title'], 'url': article['url']} 
                for article in data['articles']]
    except Exception as e:
        st.error(f"NewsAPI Error: {str(e)}")
        return []

def process_article(url, summarizer):
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        if not text or len(text.split()) < 50:
            return {
                'title': article.title or "No Title",
                'summary': "Article too short or could not extract content.",
                'url': url,
                'success': False
            }
        if len(text) > 2000:
            text = text[:2000]
        summary = summarizer(
            text,  
            min_length=60,
            truncation=True
        )[0]['summary_text']
        return {
            'title': article.title or "No Title",
            'summary': summary,
            'url': url,
            'success': True
        }
    except Exception as e:
        return {
            'title': "Error",
            'summary': f"Processing failed: {str(e)}",
            'url': url,
            'success': False
        }

def main():
    st.set_page_config(page_title="News Summarizer", layout="wide")
    st.title("News Summarizer")
    st.write("Enter a news topic to get the latest articles")

    st.sidebar.header("Settings")
    num_articles = st.sidebar.slider("Number of Articles", 1, 10, 5)

    user_input = st.text_input("News Topic",)

    if st.button("Get Summaries"):
        if not API_KEY:
            st.error("API key is missing in the code.")
            return

        with st.spinner("Fetching latest news..."):
            news_articles = get_news_links(user_input, API_KEY, num_articles)

        if not news_articles:
            st.warning("No articles found or API error occurred.")
            return

        st.subheader(f"Top {len(news_articles)} news summaries for: {user_input}")

        summarizer = load_summarizer()

        for idx, article in enumerate(news_articles, 1):
            with st.expander(f"{idx}. {article['title']}"):
                result = process_article(article['url'], summarizer)
                if result['success']:
                    st.markdown(f"**Summary:**\n{result['summary']}")
                else:
                    st.warning(result['summary'])
                st.markdown(f"[Read Full Article]({article['url']})")

if __name__ == "__main__":
    main()
