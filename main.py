import streamlit as st
import requests
from bs4 import BeautifulSoup
import trafilatura
import re
from urllib.parse import urlparse

def clean_text(text):
    """Entfernt Zitate (Text in Anführungszeichen) und bereinigt den Text"""
    # Entferne verschiedene Arten von Anführungszeichen und deren Inhalt
    text = re.sub(r'["„"].*?[""]', '', text)
    text = re.sub(r"['‚'].*?['']", '', text)
    
    # Normalisiere Whitespace
    text = ' '.join(text.split())
    return text

def extract_with_requests(url):
    """Methode 1: Einfaches Scraping mit requests und BeautifulSoup"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Entferne Scripts, Styles und andere unwichtige Elemente
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
    words1 = text1.split()
    found_matches = {}  # Speichert Start-Index -> (Länge, Text)
    
    # Finde alle möglichen Matches
    i = 0
    while i < len(words1):
        max_match_at_pos = None
        max_length_at_pos = 0
        
        # Suche das längste Match an dieser Position
        for length in range(min_words, len(words1) - i + 1):
            sequence = ' '.join(words1[i:i + length])
            if sequence in text2:
                max_match_at_pos = sequence
                max_length_at_pos = length
            else:
                # Wenn keine längere Sequenz gefunden wurde, brechen wir ab
                break
                
        if max_match_at_pos:
            found_matches[i] = (max_length_at_pos, max_match_at_pos)
            i += max_length_at_pos  # Überspringe die gematchten Wörter
        else:
            i += 1
            
    # Extrahiere nur die Matches
    return [match for _, (_, match) in found_matches.items()]

def main():
    st.title("🔍 Plagiats-Checker")
    st.write("Überprüfen Sie Text auf mögliche nicht-zitierte Übernahmen aus Webseiten.")
    
    # URL-Eingabefelder
    st.subheader("Quell-URLs eingeben")
    urls = []
    for i in range(4):
        url = st.text_input(f"URL {i+1}", key=f"url_{i}")
        if url:
            urls.append(url)
    
    # Texteingabe
    st.subheader("Zu überprüfenden Text eingeben")
    user_text = st.text_area("Ihr Text", height=200)
    
    if st.button("Auf Plagiate prüfen") and urls and user_text:
        with st.spinner("Überprüfe auf Plagiate..."):
            # Bereinige User-Text
            cleaned_user_text = clean_text(user_text)
            
            # Dictionary für gefundene Übereinstimmungen
            all_matches = {}  # URL -> [matches]
            
            # Überprüfe jede URL
            for url in urls:
                if not url.strip():
                    continue
                    
                progress_text = st.empty()
                progress_text.write(f"Analysiere {url}...")
                
                # Versuche verschiedene Scraping-Methoden
                content = extract_with_requests(url)
                if not content:
                    content = extract_with_trafilatura(url)
                
                if content:
                    # Bereinige gescrapten Text
                    cleaned_content = clean_text(content)
                    
                    # Finde Übereinstimmungen
                    matches = find_max_matching_sequences(cleaned_user_text, cleaned_content)
                    if matches:
                        all_matches[url] = matches
                        
                progress_text.empty()
            
            # Zeige Ergebnisse
            st.subheader("Gefundene Übereinstimmungen:")
            
            if all_matches:
                for url, matches in all_matches.items():
                    st.markdown(f"### Quelle: [{urlparse(url).netloc}]({url})")
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
