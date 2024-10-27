import streamlit as st
import requests
from bs4 import BeautifulSoup
import trafilatura
import re
from urllib.parse import urlparse

def clean_text(text):
    """Bereinigt den Text minimal, um Übereinstimmungen besser zu finden"""
    if not text:
        return ""
    
    # Debug-Ausgabe des Originaltexts
    st.write("Original:", text[:200])
    
    # 1. Entferne Navigation und Metadaten am Anfang/Ende
    text = re.sub(r'^(?:Home|News|Panorama|Kriminalität|Schlagzeilen|Alle|Zurück|Artikel\steilen\smit:).*?\n', '', text)
    
    # 2. Entferne Zitate
    quotes_patterns = [
        r'["\u201C\u201D\u201E\u201F].*?["\u201C\u201D\u201E\u201F]',
        r'[\u2018\u2019\u201A\u201B].*?[\u2018\u2019\u201A\u201B]',
        r"'.*?'",
        r"».*?«",
        r"›.*?‹"
    ]
    for pattern in quotes_patterns:
        text = re.sub(pattern, '', text)
    
    # 3. Normalisiere nur grundlegende Sachen
    text = text.replace('–', '-')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Debug-Ausgabe des bereinigten Texts
    st.write("Bereinigt:", text[:200])
    
    return text

def extract_with_requests(url):
    """Methode 1: Einfaches Scraping mit requests und BeautifulSoup"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Entferne mehr unwichtige Elemente
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'meta', 'link']):
            element.decompose()
            
        # Entferne Navigation und Metadaten
        for element in soup.find_all(['nav', 'header', 'footer']):
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
    if not text1 or not text2:
        return []
    
    # Debug: Zeige die ersten 200 Zeichen beider Texte
    st.write("Text1 (User) Anfang:", text1[:200])
    st.write("Text2 (Quelle) Anfang:", text2[:200])
    
    words1 = text1.split()
    words2 = text2.split()
    found_matches = {}
    
    i = 0
    while i < len(words1):
        max_match_at_pos = None
        max_length_at_pos = 0
        
        # Suche nach der längstmöglichen Übereinstimmung
        current_sequence = []
        for j in range(i, len(words1)):
            current_sequence.append(words1[j])
            current_text = ' '.join(current_sequence)
            
            # Prüfe ob die aktuelle Sequenz im Quelltext vorkommt
            if current_text in text2 and len(current_sequence) >= min_words:
                max_match_at_pos = current_text
                max_length_at_pos = len(current_sequence)
        
        if max_match_at_pos:
            found_matches[i] = (max_length_at_pos, max_match_at_pos)
            i += max_length_at_pos
        else:
            i += 1
            
    return [match for _, (_, match) in found_matches.items()]

def main():
    st.title("🔍 Plagiats-Checker")
    st.write("Überprüfen Sie Text auf mögliche nicht-zitierte Übernahmen aus Webseiten.")
    
    if 'source_texts' not in st.session_state:
        st.session_state.source_texts = [""] * 4

    sources = []
    
    st.subheader("Quell-Texte eingeben")
    
    # Layout für jede Quelle
    for i in range(4):
        # Container für URL und Button
        container = st.container()
        col1, col2 = container.columns([4, 1])
        
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
            cleaned_user_text = clean_text(user_text)
            all_matches = {}
            
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
