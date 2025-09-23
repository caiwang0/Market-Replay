from langchain_core.tools import tool
from urllib.parse import urljoin
from typing import List
from bs4 import BeautifulSoup
import requests
from datetime import date, timedelta
from newspaper import Article
import newspaper.network


@tool
async def getLatestBBCNews(limit: int) -> List[str]:
    """
    Obtain the url of the 'limit' most prominent financial articles from 
    BBC, and summarise each article, including key financial data in
    the summary. Mention the source of the summary.
    """

    def custom_get(url, **kwargs):
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        return requests.get(url, headers=headers, **kwargs)
    
    newspaper.network.get_html = custom_get
    base_url = "https://www.bbc.com"
    business_url = f"{base_url}/business"
    
    response = requests.get(business_url)
    soup = BeautifulSoup(response.text, "html.parser")

    article_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/news/article"):
            full_url = urljoin(base_url, href)
            if full_url not in article_links:
                article_links.append(full_url)
        if len(article_links) >= limit:
            break
    
    articles = []
    for url in article_links:
        article = Article(url)
        article.download()
        article.parse()
        articles.append(article.text)
    
    return articles

@tool
async def getLatestReutersNews(limit=10):
    """
    Obtain the url of the 'limit' most prominent financial articles from 
    Reuters, and summarise each article, including key financial data in
    the summary. Mention the source of the summary.
    """
    base_url = "https://www.reuters.com"
    finance_url = f"{base_url}/business/finance/"

    today = date.today() - timedelta(days=1)
    response = requests.get(finance_url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    article_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(f"{today}/"):
            full_url = urljoin(base_url, href)
            if full_url not in article_links:
                article_links.append(full_url)
        if len(article_links) >= limit:
            break
    
    articles = []
    for url in article_links:
        article = Article(url)
        article.download()
        article.parse()
        articles.append(article.text)
    
    return articles

@tool
async def getEarningsCalendar():
    """
    Get a list of upcoming Earnings Reports and their dates. 
    """
    end_date = date.today() + timedelta(days=7)
    print(end_date)

    response = requests.get(f"https://financialmodelingprep.com/stable/earnings-calendar?from={date.today()}&to={end_date}&apikey=gzYBc0wd5C1ZZV7mt2zkIKc1IN8Gkh3R")
    print(response.json())
    if response.status_code == 200:
        earnings = response.json()
        return earnings[:20]  # limit to top 20 results
    else:
        raise Exception(f"Failed to fetch: {response.status_code} - {response.text}")