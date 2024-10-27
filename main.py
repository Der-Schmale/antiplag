import streamlit as st
import requests
from bs4 import BeautifulSoup
import trafilatura
import re
from urllib.parse import urlparse

# Mindestlänge für Übereinstimmungen (in Zeichen)
STRING_LENGTH = 40

def extract_with_requests(url):
    """Methode 1: Einfaches Scraping mit requests und BeautifulSoup"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Entferne nur die wichtigsten unwichtigen Elemente
        for element in soup(['script', 'style']):
            element.decompose()
            
        # Normalisiere nur Whitespace
        text = ' '.join(soup.get_text().split())
        return text
    except Exception as e:
        print(f"Fehler beim Scraping: {e}")
        return None

def extract_with_trafilatura(url):
    """Methode 2: Scraping mit trafilatura (sehr gut für Artikel)"""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text
    except:
        return None

def find_matching_strings(text1, text2, min_length=STRING_LENGTH):
    """Findet übereinstimmende Textpassagen mit Mindestlänge"""
    matches = []
    text_length = len(text1)
    i = 0
    
    while i < text_length:
        # Nimm ein Fenster von min_length Zeichen
        current_window = text1[i:i + min_length]
        
        # Wenn dieses Fenster in text2 vorkommt, erweitere es
        if current_window in text2:
            j = i + min_length
            while j < text_length and text1[i:j+1] in text2:
                j += 1
            matches.append(text1[i:j])
            i = j  # Springe zum Ende des gefundenen Matches
        else:
            i += 1
            
    return matches

def main():
    st.title("🔍 Plagiats-Checker")
    st.write("Überprüfen Sie Text auf mögliche nicht-zitierte Übernahmen aus Webseiten.")
    
    if 'source_texts' not in st.session_state:
        st.session_state.source_texts = [""] * 4

    sources = []
    
    st.subheader("Quell-Texte eingeben")
    
    # Layout für jede Quelle
    for i in range(4):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            url = st.text_input(f"URL {i+1}", key=f"url_{i}")
        with col2:
            if st.button("Einlesen", key=f"scrape_{i}", help="Text von der URL einlesen") and url:
                content = extract_with_requests(url)
                if not content:
                    content = extract_with_trafilatura(url)
                if content:
                    st.session_state.source_texts[i] = content
                else:
                    st.error("Konnte Text nicht extrahieren.")
        
        # Textfeld für gescrapten/manuellen Text
        source_text = st.text_area(
            f"Quelltext {i+1} (eingelesen oder manuell eingeben)", 
            value=st.session_state.source_texts[i],
            key=f"text_{i}",
            height=150
        )
        
        if url.strip() or source_text.strip():
            sources.append((url, source_text))
        
        st.markdown("---")
    
    st.subheader("Zu überprüfenden Text eingeben")
    user_text = st.text_area("Ihr Text", height=200)
    
    if st.button("Auf Plagiate prüfen") and user_text and sources:
        with st.spinner("Überprüfe auf Plagiate..."):
            # Keine Textbereinigung mehr, nur Whitespace normalisieren
            user_text = ' '.join(user_text.split())
            all_matches = {}
            
            for url, source_text in sources:
                if not source_text.strip():
                    continue
                    
                source_text = ' '.join(source_text.split())
                matches = find_matching_strings(user_text, source_text)
                
                if matches:
                    source_label = url if url.strip() else "Manuell eingegebener Text"
                    all_matches[source_label] = matches
            
            st.subheader("Gefundene Übereinstimmungen:")
            
            if all_matches:
                for source, matches in all_matches.items():
                    if source.startswith('http'):
                        st.markdown(f"### Quelle: [{urlparse(source).netloc}]({source})")
                    else:
                        st.markdown(f"### Quelle: {source}")
                        
                    for match in matches:
                        st.markdown(f"**Gefundene Textpassage** ({len(match)} Zeichen):")
                        st.markdown(f"""<div style="background-color: white; padding: 10px; border: 1px solid #ccc; color: black; margin: 10px 0; font-family: monospace; white-space: pre-wrap;">
                        {match}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.success("Keine verdächtigen Übereinstimmungen gefunden!")

if __name__ == "__main__":
    main()
