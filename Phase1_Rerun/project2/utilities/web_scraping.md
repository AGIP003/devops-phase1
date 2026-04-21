Day 7 — Web Scraping

Core Idea:
Web scraping = HTTP request + HTML parsing + data extraction

requests:
- Fetch HTML
- response.status_code
- response.text

BeautifulSoup:
- Parse HTML
- find(), find_all(), select()
- Extract text and attributes

CSS Selectors:
- .class
- #id
- tag
- parent > child

Pipeline:
Request → HTML → Parse → Extract → DataFrame → Store

Ethics:
- Check robots.txt
- Respect rate limits
- Use headers
- Don’t overload servers

Project:
- Scraped headlines / quotes
- Stored in CSV
- Cleaned data

Insight:
Scraping is only useful when integrated into analysis