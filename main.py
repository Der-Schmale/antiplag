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

def find_matching_sequences(text1, text2, min_words=5):
    """Findet übereinstimmende Sequenzen mit mindestens min_words Wörtern"""
    words1 = text1.split()
    words2 = text2.split()
    matches = {}
    
    for i in range(len(words1) - min_words + 1):
        for j in range(min_words, len(words1) - i + 1):
            sequence = ' '.join(words1[i:i+j])
            if sequence in text2 and len(sequence.split()) >= min_words:
                matches[sequence] = sequence
                break
    
    return matches

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
            matches = {}
            
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
                    url_matches = find_matching_sequences(cleaned_user_text, cleaned_content)
                    
                    # Füge URL zu den Matches hinzu
                    for match in url_matches.keys():
                        matches[match] = url
                        
                progress_text.empty()
            
            # Zeige Ergebnisse
            st.subheader("Gefundene Übereinstimmungen:")
            
            if matches:
                for text, source_url in matches.items():
                    st.markdown(f"""
                    ---
                    **Stelle im User-Text:** "{text}"
                    
                    **Quelle:** [{urlparse(source_url).netloc}]({source_url})
                    """)
            else:
                st.success("Keine verdächtigen Übereinstimmungen gefunden!")

if __name__ == "__main__":
    main()
