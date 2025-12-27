#!/usr/bin/env python3
"""
Scarica EPG da Open-EPG
URL: https://www.open-epg.com/generate/56jVbhRGv6.xml
User-Agent: Mozilla Firefox
"""

import os
import sys
import gzip
import requests
from datetime import datetime

# CONFIGURAZIONE
OPENEPG_URL = "https://www.open-epg.com/generate/56jVbhRGv6.xml.gz"
CACHE_DIR = 'cache'
OUTPUT_FILE = os.path.join(CACHE_DIR, 'epg_raw.xml.gz')

# User-Agent Mozilla Firefox
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'

def download_epg():
    """Scarica EPG compresso da Open-EPG"""
    
    print(f"Downloading EPG...")
    print(f"   URL: {OPENEPG_URL}")
    print(f"   User-Agent: Mozilla Firefox\n")
    
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
        
        # Salva file compresso
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(response.content)
        
        # Verifica dimensione
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"Downloaded: {size_mb:.2f} MB")
        
        # Decomprimi
        with gzip.open(OUTPUT_FILE, 'rb') as f_in:
            xml_content = f_in.read()
            
            xml_file = OUTPUT_FILE.replace('.gz', '')
            with open(xml_file, 'wb') as f_out:
                f_out.write(xml_content)
        
        print(f"Decompressed: {len(xml_content) / (1024*1024):.2f} MB")
        return True
        
    except requests.RequestException as e:
        print(f"Errore download: {e}")
        return False
    except Exception as e:
        print(f"Errore: {e}")
        return False

if __name__ == '__main__':
    success = download_epg()
    sys.exit(0 if success else 1)
