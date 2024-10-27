import streamlit as st
import requests
from bs4 import BeautifulSoup
import trafilatura
import re
from urllib.parse import urlparse

def clean_text(text):
    """Entfernt Zitate (Text in Anführungszeichen) und bereinigt den Text"""
    if not text:  # Überprüfe auf None oder leeren String
        return ""
    text = re.sub(r'["„"].*?[""]', '', text)
    text = re.sub(r"['‚'].*?['']", '', text)
    text = ' '.join(text.split())
    return text

def extract_with_requests(url):
    """Methode 1: Einfaches Scraping mit requests und BeautifulSoup"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
            
        return ' '.join(soup.get_text().split())
    except:
        return None

def extract_with_trafilatura(url):
    """Methode 2: Scraping mit trafilatura (sehr gut für Artikel)"""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except:
        return None

def find_max_matching_sequences(text1, text2, min_words=5):
    """Findet die maximalen, nicht-überlappenden Sequenzen"""
    if not text1 or not text2:  # Überprüfe auf leere Texte
        return []
    
    words1 = text1.split()
    found_matches = {}
    
    i = 0
    while i < len(words1):
        max_match_at_pos = None
        max_length_at_pos = 0
        
        for length in range(min_words, len(words1) - i + 1):
            sequence = ' '.join(words1[i:i + length])
            if sequence in text2:
                max_match_at_pos = sequence
                max_length_at_pos = length
            else:
                break
                
        if max_match_at_pos:
            found_matches[i] = (max_length_at_pos, max_match_at_pos)
            i += max_length_at_pos
        else:
            i += 1
            
    return [match for _, (_, match) in found_matches.items()]

def main():
    st.title("🔍 Plagiats-Checker")
    st.write("Überprüfen Sie Text auf mögliche nicht-zitierte Übernahmen aus Webseiten.")
    
    # Container für URL-Eingaben und zugehörige Texte
    st.subheader("Quell-Texte eingeben")
    
    # Dictionary für die gescrapten/eingegebenen Texte
    if 'source_texts' not in st.session_state:
        st.session_state.source_texts = [""] * 4

    sources = []  # Liste für URLs und ihre Texte
    
    # Erstelle 4 Eingabeblöcke
    for i in range(4):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            url = st.text_input(f"URL {i+1}", key=f"url_{i}")
        with col2:
            if st.button("Scrapen", key=f"scrape_{i}") and url:
                with st.spinner(f"Scrape URL {i+1}..."):
                    content = extract_with_requests(url)
                    if not content:
                        content = extract_with_trafilatura(url)
                    if content:
                        st.session_state.source_texts[i] = content
                        st.success("Text erfolgreich gescraped!")
                    else:
                        st.error("Konnte Text nicht extrahieren.")
        
        # Textfeld für gescrapten/manuellen Text
        source_text = st.text_area(
            f"Quelltext {i+1} (gescraped oder manuell eingeben)", 
            value=st.session_state.source_texts[i],
            key=f"text_{i}",
            height=150
        )
        
        # Speichere URL und Text wenn mindestens eins von beiden vorhanden
        if url.strip() or source_text.strip():
            sources.append((url, source_text))
        
        st.markdown("---")
    
    # Texteingabe für zu prüfenden Text
    st.subheader("Zu überprüfenden Text eingeben")
    user_text = st.text_area("Ihr Text", height=200)
    
    if st.button("Auf Plagiate prüfen") and user_text and sources:
        with st.spinner("Überprüfe auf Plagiate..."):
            cleaned_user_text = clean_text(user_text)
            all_matches = {}  # URL/Quelle -> [matches]
            
            for url, source_text in sources:
                if not source_text.strip():
                    continue
                    
                cleaned_source = clean_text(source_text)
                matches = find_max_matching_sequences(cleaned_user_text, cleaned_source)
                
                if matches:
                    source_label = url if url.strip() else "Manuell eingegebener Text"
                    all_matches[source_label] = matches
            
            st.subheader("Gefundene Übereinstimmungen:")
            
            if all_matches:
                for source, matches in all_matches.items():
                    # Erstelle klickbaren Link nur wenn es eine URL ist
                    if source.startswith('http'):
                        st.markdown(f"### Quelle: [{urlparse(source).netloc}]({source})")
                    else:
                        st.markdown(f"### Quelle: {source}")
                        
                    for match in matches:
                        st.markdown(f"""
                        **Gefundene Textpassage** ({len(match.split())} Wörter):
                        ```
                        {match}
                        ```
                        """)
                    st.markdown("---")
            else:
                st.success("Keine verdächtigen Übereinstimmungen gefunden!")

if __name__ == "__main__":
    main()
