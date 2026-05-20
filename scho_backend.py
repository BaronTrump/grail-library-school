import os
import re
import json
from openai import OpenAI

#########################
# 1) CONFIG
#########################

client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key=os.environ.get("AIML_API_KEY", "ac2a1d57301e41ac9d2312ff708daab5"),
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

#########################
# 2) LOAD TEXTS
#########################

BIBLE_BOOKS = []
QURAN_DATA = []
TEXT_STORE = {}


def load_all_texts():
    """Load all religious texts from data directory."""
    global BIBLE_BOOKS, QURAN_DATA, TEXT_STORE
    
    # Load KJV books list
    books_file = os.path.join(DATA_DIR, "kjv_books.json")
    if os.path.exists(books_file):
        with open(books_file, "r", encoding="utf-8") as f:
            BIBLE_BOOKS = json.load(f)
    
    # Load Quran
    quran_file = os.path.join(DATA_DIR, "quran_en.json")
    if os.path.exists(quran_file):
        with open(quran_file, "r", encoding="utf-8") as f:
            quran_data = json.load(f)
            # Convert to searchable format
            for surah in quran_data:
                TEXT_STORE[f"Quran {surah.get('chapter', '?')}"] = surah.get("verses", [])
    
    # Load individual Bible books
    for book in BIBLE_BOOKS:
        book_file = os.path.join(DATA_DIR, f"{book.lower().replace(' ', '_')}.json")
        if os.path.exists(book_file):
            try:
                with open(book_file, "r", encoding="utf-8") as f:
                    book_data = json.load(f)
                    TEXT_STORE[book] = book_data
            except Exception as e:
                print(f"Error loading {book}: {e}")
    
    print(f"Loaded {len(TEXT_STORE)} texts")


def search_texts(query, source=None, limit=5):
    """Search across all loaded texts."""
    results = []
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Filter sources if specified
    sources_to_search = []
    if source:
        for key in TEXT_STORE:
            if source.lower() in key.lower():
                sources_to_search.append(key)
    else:
        sources_to_search = list(TEXT_STORE.keys())
    
    for source_key in sources_to_search:
        text_data = TEXT_STORE.get(source_key, [])
        if isinstance(text_data, list):
            for item in text_data:
                if isinstance(item, dict):
                    # Handle Bible format
                    text = item.get("text", "")
                    chapter = item.get("chapter", "")
                    verse = item.get("verse", "")
                    ref = f"{source_key} {chapter}:{verse}" if chapter else source_key
                elif isinstance(item, dict):
                    # Handle Quran format  
                    verses = item.get("verses", [])
                    for v in verses:
                        text = v.get("text", v.get("verse", ""))
                        ref = f"{source_key} {v.get('verse', '')}"
                        text_lower = text.lower()
                        matches = sum(1 for w in query_words if w in text_lower)
                        if matches > 0:
                            results.append({
                                "source": source_key,
                                "reference": ref,
                                "text": text,
                                "score": matches
                            })
                else:
                    # Plain text
                    text = str(item)
                    text_lower = text.lower()
                    matches = sum(1 for w in query_words if w in text_lower)
                    if matches > 0:
                        results.append({
                            "source": source_key,
                            "text": text,
                            "score": matches
                        })
        elif isinstance(text_data, dict):
            # Dict format (Quran surah)
            chapters = text_data.get("surahs", [text_data])
            for ch in chapters:
                verses = ch.get("verses", [])
                for v in verses:
                    text = v.get("text", v.get("translation", ""))
                    text_lower = text.lower()
                    matches = sum(1 for w in query_words if w in text_lower)
                    if matches > 0:
                        results.append({
                            "source": f"Quran {ch.get('id', '?')}",
                            "reference": f"Quran {ch.get('id', '?')}:{v.get('verse', '')}",
                            "text": text,
                            "score": matches
                        })
    
    # Sort by score and limit
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:limit]


def format_context(results, max_chars=3000):
    """Format search results as context for AI."""
    context_parts = []
    total_chars = 0
    
    for r in results:
        ref = r.get("reference", r.get("source", ""))
        text = r.get("text", "")
        part = f"[{ref}] {text}"
        
        if total_chars + len(part) > max_chars:
            break
        context_parts.append(part)
        total_chars += len(part)
    
    return "\n\n".join(context_parts)


def generate_answer(context, user_query, sources):
    """Call AI model with context."""
    if not context:
        return "No relevant information found in the religious texts."
    
    source_info = ", ".join(sources) if sources else "various religious texts"
    
    messages = [
        {
            "role": "user",
            "content": (
                f"You are a knowledgeable religious scholar. Use ONLY the provided scriptural references "
                f"from {source_info} to answer the user's question accurately.\n\n"
                f"Provide the specific verse/chapter references when citing.\n\n"
                f"Scriptural References:\n{context}\n\n"
                f"User Question: {user_query}"
            )
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1",
            messages=messages
        )
        return response.choices[0].message.content if response.choices else "No response from the API."
    except Exception as e:
        return f"Error: {e}"


def answer_user_query(query, source=None):
    """
    Search religious texts and answer user question.
    source: 'bible', 'quran', 'talmud', or None for all
    """
    if not TEXT_STORE:
        load_all_texts()
    
    if not TEXT_STORE:
        return "No religious texts loaded. Please ensure data files are in the data/ folder."
    
    # Map source names
    source_map = {
        "bible": [" Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", 
                 "Judges", "Ruth", "Samuel", "Kings", "Chronicles", "Ezra", "Nehemiah", 
                 "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song", "Isaiah",
                 "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
                 "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
                 "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
                 "Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", 
                 "Thessalonians", "Timothy", "Titus", "Philemon", "Hebrews", "James", 
                 "Peter", "John", "Jude", "Revelation"],
        "quran": ["Quran"],
        "talmud": ["Talmud"]
    }
    
    sources_to_use = None
    if source and source.lower() in source_map:
        sources_to_use = source_map[source.lower()]
    
    results = search_texts(query, source=sources_to_use)
    
    if not results:
        return f"No relevant verses found for '{query}'. Try a different search."
    
    context = format_context(results)
    
    return generate_answer(context, query, sources_to_use or ["loaded religious texts"])


# Initialize on module load
try:
    load_all_texts()
except Exception as e:
    print(f"Warning: Could not load texts: {e}")