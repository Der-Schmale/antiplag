def clean_text(text):
    """Bereinigt den Text gründlicher"""
    if not text:
        return ""
    
    # Debug-Ausgabe des Originaltexts
    st.write("Original:", text[:200])
    
    # 1. Entferne häufige Navigations- und Metadatenelemente
    nav_patterns = [
        r'Home\s*News',
        r'Schlagzeilen\s*Alle',
        r'Artikel teilen mit',
        r'Lesen Sie mehr',
        r'zum Thema',
        r'(?:Panorama|Kriminalität)',
        r'\d{2}\.\d{2}\.\d{4}',  # Datumsmuster
        r'\d{2}:\d{2}\s+Uhr',    # Uhrzeitmuster
        r'[A-Z][a-z]+:\s*[A-Z]'  # Typische Nachrichtenüberschriften
    ]
    
    for pattern in nav_patterns:
        text = re.sub(pattern, '', text)
    
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
    
    # 3. Entferne doppelte Textpassagen
    text = re.sub(r'(.{50,}?)\1+', r'\1', text)  # Entfernt längere wiederholte Passagen
    
    # 4. Normalisiere Satzzeichen und Whitespace
    text = text.replace('–', '-')
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Füge Leerzeichen nach Satzzeichen ein
    text = re.sub(r'[,:]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 5. Entferne kurze Schlagzeilen am Ende
    text = re.sub(r'(?:[A-Z][^.!?]{10,50}(?:[.!?]|\s|$))+$', '', text)
    
    text = text.strip()
    
    # Debug-Ausgabe des bereinigten Texts
    st.write("Bereinigt:", text[:200])
    
    return text
