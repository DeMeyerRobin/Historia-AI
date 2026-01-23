# utils/tools.py
import requests
import re
from html import unescape
from typing import Optional
from urllib.parse import quote

try:
    import wikipedia
    from wikipedia.exceptions import DisambiguationError, PageError
except ImportError:  # pragma: no cover - optional dependency
    wikipedia = None
    DisambiguationError = PageError = Exception


WIKIPEDIA_ARTICLE_CHAR_LIMIT = 4500
BRITANNICA_BASE_URL = "https://www.britannica.com"

def _clean_query(q: str) -> str:
    # Remove junk the planner may include, like <...> and question marks
    q = (q or "").strip()
    q = q.replace("<", "").replace(">", "")
    q = q.strip().strip(" ?!./\\\"'")
    return q

def _truncate_article(text: str) -> str:
    snippet = text.strip()
    if len(snippet) <= WIKIPEDIA_ARTICLE_CHAR_LIMIT:
        return snippet
    truncated = snippet[:WIKIPEDIA_ARTICLE_CHAR_LIMIT]
    # Avoid chopping mid-sentence if we can
    last_break = max(truncated.rfind("\n"), truncated.rfind("."))
    if last_break > 2000:  # ensure we actually truncate meaningfully
        truncated = truncated[:last_break]
    return truncated.strip() + "..."

def _strip_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return unescape(cleaned).strip()

def _fetch_full_article(query: str, sentences: int):
    if not wikipedia:
        return None

    wikipedia.set_lang("en")

    try:
        page = wikipedia.page(query, auto_suggest=True, preload=False)
    except DisambiguationError as err:
        if not err.options:
            raise
        page = wikipedia.page(err.options[0], auto_suggest=False, preload=False)
    except PageError:
        results = wikipedia.search(query, results=1)
        if not results:
            raise
        page = wikipedia.page(results[0], auto_suggest=False, preload=False)

    return {
        "title": page.title,
        "url": page.url,
        "summary": wikipedia.summary(page.title, sentences=sentences),
        "content": _truncate_article(page.content),
    }


def wikipedia_summary(query: str, sentences: int = 3) -> str:
    query_clean = _clean_query(query)
    if not query_clean:
        return "[wiki] Empty query."

    headers = {
        "User-Agent": "myfirstbot/1.0 (Discord demo bot)",
        "Accept": "application/json",
        "Accept-Language": "en",
        "DNT": "1",
    }

    def fetch_summary(title: str):
        title_enc = quote(title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_enc}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None, None
        data = r.json()
        return data.get("title"), data.get("extract")

    try:
        # Try direct
        title, extract = fetch_summary(query_clean)

        # Fallback: opensearch
        if not extract:
            api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query_clean,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            }
            r = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = r.json()
            if not data[1]:
                return f"[wiki] No results for '{query_clean}'."

            title = data[1][0]
            title, extract = fetch_summary(title)

        article_url = None
        full_article_block = ""

        if not extract and not wikipedia:
            return f"[wiki] Failed to retrieve summary for '{query_clean}'."

        if wikipedia:
            try:
                article_data = _fetch_full_article(title or query_clean, sentences)
                if article_data:
                    title = article_data.get("title", title)
                    article_url = article_data.get("url")
                    extracted_summary = article_data.get("summary")
                    full_content = article_data.get("content")
                    if extracted_summary:
                        extract = extracted_summary
                    if full_content:
                        full_article_block = f"\n\n📝 **Full Article Excerpt:**\n{full_content}"
            except Exception as err:  # pragma: no cover - best effort addon
                full_article_block = f"\n\n⚠️ Unable to fetch full article via library: {type(err).__name__}"

        if not extract:
            return f"[wiki] Failed to retrieve summary for '{query_clean}'."

        parts = extract.split(". ")
        summary = ". ".join(parts[:sentences]).strip()
        if summary and not summary.endswith("."):
            summary += "."

        if not article_url:
            article_url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"

        return (
            f"📚 **Wikipedia Article Used:** {title}\n"
            f"🔗 {article_url}\n\n"
            f"🧾 **Summary:**\n{summary}" + full_article_block
        )

    except Exception as e:
        return f"[wiki] error: {type(e).__name__}: {e}"


def _extract_britannica_article_url(html_text: str) -> Optional[str]:
    if not html_text:
        return None
    patterns = [
        r'href="(/topic/[^"#?]+)"',
        r'href="(/event/[^"#?]+)"',
        r'href="(/biography/[^"#?]+)"',
        r'href="(/place/[^"#?]+)"',
        r'href="(/science/[^"#?]+)"',
        r'href="(/technology/[^"#?]+)"',
        r'href="(/art/[^"#?]+)"',
        r'href="(/animal/[^"#?]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text)
        if match:
            return f"{BRITANNICA_BASE_URL}{match.group(1)}"
    return None


def _extract_britannica_summary(html_text: str, sentences: int) -> str:
    if not html_text:
        return ""
    paragraph_match = re.search(r'<p class="topic-paragraph[^"]*">(.*?)</p>', html_text, re.DOTALL)
    if paragraph_match:
        raw_text = _strip_html(paragraph_match.group(1))
    else:
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', html_text)
        raw_text = _strip_html(desc_match.group(1)) if desc_match else ""

    if not raw_text:
        return ""
    parts = [p.strip() for p in raw_text.split(". ") if p.strip()]
    summary = ". ".join(parts[:sentences]).strip()
    if summary and not summary.endswith("."):
        summary += "."
    return summary


def _check_article_relevance(query: str, title: str, url: str, summary: str) -> bool:
    """
    Check if the article found is actually relevant to the query.
    Returns True if relevant, False if it seems like the wrong article.
    """
    query_lower = query.lower()
    title_lower = title.lower()
    summary_lower = summary.lower()
    
    # Extract meaningful keywords from query (ignore common stopwords)
    stopwords = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but', 'treaty', 'agreement'}
    query_words = [w.strip('.,!?()[]') for w in query_lower.split()]
    query_keywords = [w for w in query_words if w not in stopwords and len(w) > 2]
    
    if not query_keywords:
        return True  # Can't determine, assume it's ok
    
    # Count how many query keywords appear in title or summary
    matches = 0
    for keyword in query_keywords:
        if keyword in title_lower or keyword in summary_lower:
            matches += 1
    
    # Consider it relevant if at least 50% of keywords match
    relevance_threshold = len(query_keywords) * 0.5
    
    if matches >= relevance_threshold:
        return True
    
    # Special case: Check if article is about a completely different geographic location or era
    # For example, "Treaty of Lisbon" query but finding Portugal-Spain treaty instead of EU treaty
    
    # If query contains modern indicators but article only mentions old dates
    modern_indicators = ['european union', 'eu ', ' eu', 'modern', 'contemporary', '19', '20']
    has_modern_indicator = any(ind in query_lower for ind in modern_indicators)
    
    old_date_pattern = r'\b(14|15|16|17|18)\d{2}\b'
    modern_date_pattern = r'\b(19|20)\d{2}\b'
    
    has_old_dates = bool(re.search(old_date_pattern, f"{title} {summary}"))
    has_modern_dates = bool(re.search(modern_date_pattern, f"{title} {summary}"))
    
    # If query suggests modern content but article only has old dates, it's suspicious
    if has_modern_indicator and has_old_dates and not has_modern_dates:
        return False
    
    # Otherwise, if we have some keyword matches, consider it relevant
    return matches > 0


def _generate_alternative_queries(query: str) -> list:
    """
    Generate alternative phrasings of a query to help find the right article.
    """
    alternatives = []
    
    # Strategy 1: Reverse word order for "X of Y" patterns (e.g., "Treaty of Lisbon" → "Lisbon Treaty")
    of_pattern = r'^(\w+(?:\s+\w+)?)\s+of\s+(.+)$'
    match = re.match(of_pattern, query, re.IGNORECASE)
    if match:
        first_part = match.group(1)
        second_part = match.group(2)
        alternatives.append(f"{second_part} {first_part}")
    
    # Strategy 2: Add "European Union" context if query contains EU-related terms
    eu_indicators = ['lisbon', 'maastricht', 'rome', 'amsterdam', 'nice']
    if any(indicator in query.lower() for indicator in eu_indicators):
        if 'european union' not in query.lower() and 'eu' not in query.lower():
            alternatives.append(f"European Union {query}")
            alternatives.append(f"EU {query}")
    
    # Strategy 3: Add "modern" or "contemporary" for treaties/agreements
    if any(term in query.lower() for term in ['treaty', 'agreement', 'accord', 'convention']):
        if not any(year in query for year in ['19', '20']):  # No modern year mentioned
            alternatives.append(f"modern {query}")
    
    # Strategy 4: Remove "Treaty of" or "Agreement of" prefix
    prefixes_to_remove = [r'^treaty of\s+', r'^agreement of\s+', r'^convention of\s+']
    for prefix_pattern in prefixes_to_remove:
        alt = re.sub(prefix_pattern, '', query, flags=re.IGNORECASE).strip()
        if alt != query and alt:
            alternatives.append(alt)
    
    return alternatives


def britannica_summary(query: str, sentences: int = 3) -> str:
    query_clean = _clean_query(query)
    if not query_clean:
        return "[britannica] Empty query."

    headers = {
        "User-Agent": "myfirstbot/1.0 (Discord demo bot)",
        "Accept": "text/html",
        "Accept-Language": "en",
        "DNT": "1",
    }

    def attempt_search(search_query: str):
        """Helper to perform a single search attempt."""
        try:
            search_url = f"{BRITANNICA_BASE_URL}/search?query={quote(search_query)}"
            search_response = requests.get(search_url, headers=headers, timeout=10)
            if search_response.status_code != 200:
                return None, None, None, None

            article_url = _extract_britannica_article_url(search_response.text)
            if not article_url:
                return None, None, None, None

            article_response = requests.get(article_url, headers=headers, timeout=10)
            if article_response.status_code != 200:
                return None, None, None, None

            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', article_response.text)
            title = _strip_html(title_match.group(1)) if title_match else search_query

            summary = _extract_britannica_summary(article_response.text, sentences)
            
            return article_url, title, summary, article_response.text
        except Exception:
            return None, None, None, None

    try:
        # First attempt with original query
        article_url, title, summary, html = attempt_search(query_clean)
        
        # Check if result seems irrelevant to the query
        if article_url and title and summary:
            is_relevant = _check_article_relevance(query_clean, title, article_url, summary)
            
            if not is_relevant:
                print(f"[britannica] Found '{title}' but it doesn't seem relevant to '{query_clean}'. Trying alternatives...")
                
                # Generate and try alternative queries (limit to 2 attempts)
                alternatives = _generate_alternative_queries(query_clean)
                max_retries = 2
                retry_count = 0
                
                for alt_query in alternatives[:max_retries]:
                    retry_count += 1
                    print(f"[britannica] Retry {retry_count}/{max_retries}: Trying '{alt_query}'")
                    alt_url, alt_title, alt_summary, alt_html = attempt_search(alt_query)
                    
                    if alt_url and alt_title and alt_summary:
                        # Check if the alternative is more relevant
                        if _check_article_relevance(query_clean, alt_title, alt_url, alt_summary):
                            print(f"[britannica] Found better match: '{alt_title}'")
                            article_url, title, summary = alt_url, alt_title, alt_summary
                            break
                        else:
                            print(f"[britannica] Alternative '{alt_title}' also not very relevant...")
                
                # If we still don't have a good match after retries, use the original result anyway
                if retry_count == max_retries:
                    print(f"[britannica] Using original result '{title}' after {max_retries} retries")

        if not article_url:
            return f"[britannica] No results for '{query_clean}'."
        
        if not summary:
            return f"[britannica] Failed to retrieve summary for '{query_clean}'."

        return (
            f"📘 **Encyclopaedia Britannica Article Used:** {title}\n"
            f"🔗 {article_url}\n\n"
            f"🧾 **Summary:**\n{summary}"
        )

    except Exception as e:
        return f"[britannica] error: {type(e).__name__}: {e}"



def lightweight_factcheck(claim: str, evidence: str) -> str:
    """
    Demo-grade fact-check:
    keyword overlap between claim and evidence.
    """
    def norm_words(s: str):
        out = []
        for w in s.lower().split():
            w = w.strip(".,!?()[]{}:;\"'`")
            if len(w) >= 5:
                out.append(w)
        return set(out)

    c = norm_words(claim)
    e = norm_words(evidence)

    hits = sorted(c.intersection(e))
    if len(hits) >= 3:
        return f"✅ Supported (keyword overlap: {', '.join(hits[:10])})"
    if len(hits) >= 1:
        return f"⚠️ Weak support (keyword overlap: {', '.join(hits[:10])})"
    return "❌ Not supported by evidence (no meaningful keyword overlap)"
