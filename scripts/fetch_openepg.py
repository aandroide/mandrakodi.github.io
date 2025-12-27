#!/usr/bin/env python3
"""
Scarica EPG da Open-EPG
URL: https://www.open-epg.com/generate/56jVbhRGv6.xml (XML diretto, NON zippato)
User-Agent: Mozilla Firefox
"""

import os
import sys
import requests
from datetime import datetime

# CONFIGURAZIONE - Il tuo EPG (XML NON compresso!)
OPENEPG_URL = "https://www.open-epg.com/generate/56jVbhRGv6.xml"

CACHE_DIR = 'cache'
OUTPUT_FILE = os.path.join(CACHE_DIR, 'epg_raw.xml')

# User-Agent Mozilla Firefox
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'

def download_epg():
    """Scarica EPG XML da Open-EPG"""
    
    print(f" Downloading EPG...")
    print(f"   URL: {OPENEPG_URL}")
    print(f"   User-Agent: Mozilla Firefox")
    print(f"   Format: XML (non-compressed)\n")
    
    try:
        # Headers browser reale
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(OPENEPG_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Salva XML diretto
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(response.content)
        
        # Verifica dimensione
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f" Downloaded: {size_mb:.2f} MB")
        
        # Verifica che sia XML valido
        if response.content.startswith(b'<?xml'):
            print(f" Valid XML file")
        else:
            print(f" Warning: File doesn't start with XML header")
        
        return True
        
    except requests.RequestException as e:
        print(f" Errore download: {e}")
        return False
    except Exception as e:
        print(f" Errore: {e}")
        return False

if __name__ == '__main__':
    success = download_epg()
    sys.exit(0 if success else 1)
