# utils/tools.py
import requests
from urllib.parse import quote

try:
    import wikipedia
    from wikipedia.exceptions import DisambiguationError, PageError
except ImportError:  # pragma: no cover - optional dependency
    wikipedia = None
    DisambiguationError = PageError = Exception


WIKIPEDIA_ARTICLE_CHAR_LIMIT = 4500

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
