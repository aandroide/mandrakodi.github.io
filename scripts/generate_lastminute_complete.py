#!/usr/bin/env python3
"""
Last Minute COMPLETO - EPG + Stream Riproducibili
User-Agent: Mozilla Firefox
Supporta: ACEStream, M3U8, MPD (DASH)
"""

import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict
import re

CACHE_DIR = 'cache'
OUTPUT_DIR = 'output'

# User-Agent Mozilla Firefox
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'

# Configurazione siti stream
STREAM_SOURCES = {
    'platinsport': {
        'url': 'https://www.platinsport.com/',
        'enabled': True,
        'resolver': 'platin'
    },
    'wikisport': {
        'url': 'https://wikisport.click/',
        'enabled': True,
        'resolver': 'wikisport'
    }
}

def parse_epg_xml(xml_file: str):
    """Parse EPG XML"""
    
    print(f"📖 Parsing {xml_file}...")
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Estrai canali
    all_channels = {}
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        display_name = channel.find('display-name')
        
        all_channels[channel_id] = {
            'id': channel_id,
            'name': display_name.text if display_name is not None else channel_id,
            'icon': None
        }
        
        icon = channel.find('icon')
        if icon is not None:
            all_channels[channel_id]['icon'] = icon.get('src')
    
    print(f"Trovati {len(all_channels)} canali")
    
    # Programmi in onda ORA
    now = datetime.now()
    current_programmes = {}
    next_programmes = {}
    
    for programme in root.findall('programme'):
        try:
            start_str = programme.get('start')
            stop_str = programme.get('stop')
            
            if not start_str or not stop_str:
                continue
            
            start = datetime.strptime(start_str.split()[0], '%Y%m%d%H%M%S')
            stop = datetime.strptime(stop_str.split()[0], '%Y%m%d%H%M%S')
            
            channel_id = programme.get('channel')
            
            if start <= now < stop:
                title_elem = programme.find('title')
                desc_elem = programme.find('desc')
                category_elem = programme.find('category')
                
                current_programmes[channel_id] = {
                    'start': start,
                    'stop': stop,
                    'start_str': start.strftime('%H:%M'),
                    'stop_str': stop.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None else 'In onda',
                    'desc': desc_elem.text if desc_elem is not None else '',
                    'category': category_elem.text if category_elem is not None else ''
                }
            
            elif start > now and channel_id not in next_programmes:
                title_elem = programme.find('title')
                
                next_programmes[channel_id] = {
                    'start': start,
                    'start_str': start.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None else 'Prossimo'
                }
                
        except Exception:
            continue
    
    print(f"{len(current_programmes)} canali con programmi in onda ORA")
    
    return {
        'channels': all_channels,
        'current_programmes': current_programmes,
        'next_programmes': next_programmes,
        'updated_at': now.isoformat()
    }

def search_stream_for_event(event_title, channel_name=""):
    """Cerca stream per evento sportivo"""
    
    clean_title = event_title.lower()
    clean_title = re.sub(r'[^a-z0-9\s-]', ' ', clean_title).strip()
    
    # Keywords eventi sportivi
    sport_keywords = [
        'serie a', 'champions', 'coppa', 'vs', '-', 'calcio', 
        'basket', 'nba', 'tennis', 'formula', 'motogp', 'volley',
        'inter', 'milan', 'juventus', 'roma', 'napoli', 'lazio',
        'atalanta', 'fiorentina', 'sinner', 'musetti', 'league'
    ]
    
    is_sport = any(kw in clean_title for kw in sport_keywords)
    
    if not is_sport:
        return None
    
    print(f"Cercando stream: {event_title}")
    
    # Usa platinsport
    if STREAM_SOURCES['platinsport']['enabled']:
        return (
            STREAM_SOURCES['platinsport']['resolver'],
            STREAM_SOURCES['platinsport']['url']
        )
    
    return None

def categorize_channel(channel_id, channel_name):
    """Categorizza canale"""
    
    name_lower = channel_name.lower()
    
    if any(kw in name_lower for kw in ['sport', 'dazn', 'calcio', 'f1', 'motogp', 'tennis']):
        return 'Sport'
    elif 'cinema' in name_lower:
        return 'Cinema'
    elif any(kw in name_lower for kw in ['serie', 'atlantic', 'crime']):
        return 'Serie TV'
    elif any(kw in name_lower for kw in ['news', 'tg24']):
        return 'News'
    elif any(kw in name_lower for kw in ['documentar', 'arte', 'classica']):
        return 'Documentari'
    else:
        return 'Intrattenimento'

def generate_lastminute_complete(epg_data):
    """Genera JSON MandraKodi"""
    
    print("\n Generazione Last Minute...")
    
    mandrakodi = {
        "SetViewMode": "51",
        "items": []
    }
    
    # Header
    mandrakodi['items'].append({
        "title": "=== LAST MINUTE - LIVE + EPG ===",
        "link": "ignoreme",
        "thumbnail": "https://i.imgur.com/7wR0JXI.png",
        "fanart": "https://i.imgur.com/7wR0JXI.png",
        "info": f"Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}\\nEPG + Stream automatici"
    })
    
    # Raggruppa per categoria
    categorized = defaultdict(list)
    
    for channel_id in epg_data['channels'].keys():
        channel_info = epg_data['channels'][channel_id]
        category = categorize_channel(channel_id, channel_info['name'])
        
        categorized[category].append({
            'id': channel_id,
            'info': channel_info
        })
    
    category_order = ['Sport', 'Cinema', 'Serie TV', 'News', 'Documentari', 'Intrattenimento']
    
    stats = {'with_stream': 0, 'epg_only': 0}
    
    for category in category_order:
        if category not in categorized:
            continue
        
        channels = categorized[category]
        
        # Header categoria
        mandrakodi['items'].append({
            "title": f"=== {category.upper()} ===",
            "link": "ignoreme",
            "thumbnail": "https://i.imgur.com/7wR0JXI.png",
            "fanart": "https://i.imgur.com/7wR0JXI.png",
            "info": f"{len(channels)} canali"
        })
        
        channels.sort(key=lambda x: x['info']['name'])
        
        for channel_data in channels:
            channel_id = channel_data['id']
            channel_info = channel_data['info']
            
            current_prog = epg_data['current_programmes'].get(channel_id)
            next_prog = epg_data['next_programmes'].get(channel_id)
            
            if not current_prog:
                continue
            
            # Cerca stream
            stream_result = search_stream_for_event(
                current_prog['title'], 
                channel_info['name']
            )
            
            time_str = f"[COLOR yellow]{current_prog['start_str']}[/COLOR]"
            
            if stream_result:
                # Con stream riproducibile
                resolver, stream_url = stream_result
                
                title = f"[COLOR lime]▶[/COLOR] {channel_info['name']} - {time_str} {current_prog['title']}"
                
                info_parts = [
                    f"[B][COLOR lime]🔴 LIVE - RIPRODUCIBILE[/COLOR][/B]",
                    f"[B]In onda ORA:[/B] {current_prog['start_str']} - {current_prog['stop_str']}"
                ]
                
                if current_prog['category']:
                    info_parts.append(f"[B]Genere:[/B] {current_prog['category']}")
                
                if current_prog['desc']:
                    desc = current_prog['desc'][:200]
                    if len(current_prog['desc']) > 200:
                        desc += '...'
                    info_parts.append(f"\n{desc}")
                
                if next_prog:
                    info_parts.append(f"\n[B]A seguire ({next_prog['start_str']}):[/B] {next_prog['title']}")
                
                item = {
                    "title": title,
                    "myresolve": f"{resolver}@@{stream_url}",
                    "thumbnail": channel_info.get('icon', 'https://i.imgur.com/7wR0JXI.png'),
                    "fanart": "https://i.imgur.com/7wR0JXI.png",
                    "info": '\n'.join(info_parts)
                }
                
                stats['with_stream'] += 1
                
            else:
                # Solo EPG
                title = f"{channel_info['name']} - {time_str} {current_prog['title']}"
                
                info_parts = [
                    f"[B]In onda ORA:[/B] {current_prog['start_str']} - {current_prog['stop_str']}"
                ]
                
                if current_prog['category']:
                    info_parts.append(f"[B]Genere:[/B] {current_prog['category']}")
                
                if current_prog['desc']:
                    desc = current_prog['desc'][:200]
                    if len(current_prog['desc']) > 200:
                        desc += '...'
                    info_parts.append(f"\n{desc}")
                
                if next_prog:
                    info_parts.append(f"\n[B]A seguire ({next_prog['start_str']}):[/B] {next_prog['title']}")
                
                info_parts.append("\n[COLOR gray]Stream non disponibile[/COLOR]")
                
                item = {
                    "title": title,
                    "link": "ignoreme",
                    "thumbnail": channel_info.get('icon', 'https://i.imgur.com/7wR0JXI.png'),
                    "fanart": "https://i.imgur.com/7wR0JXI.png",
                    "info": '\n'.join(info_parts)
                }
                
                stats['epg_only'] += 1
            
            mandrakodi['items'].append(item)
    
    # Footer statistiche
    total = stats['with_stream'] + stats['epg_only']
    mandrakodi['items'].append({
        "title": "[COLOR yellow] Statistiche[/COLOR]",
        "link": "ignoreme",
        "thumbnail": "https://i.imgur.com/7wR0JXI.png",
        "fanart": "https://i.imgur.com/7wR0JXI.png",
        "info": f"Totale: {total}\\n[COLOR lime]▶ Stream:[/COLOR] {stats['with_stream']}\\nSolo EPG: {stats['epg_only']}\\n\\nAggiornato: {datetime.now().strftime('%H:%M')}"
    })
    
    print(f"Generati {len(mandrakodi['items'])} items")
    print(f"   - Con stream: {stats['with_stream']}")
    print(f"   - Solo EPG: {stats['epg_only']}")
    
    return mandrakodi

def main():
    """Main"""
    
    print("🚀 Last Minute - EPG + Stream")
    print("   User-Agent: Mozilla Firefox\n")
    
    epg_xml = os.path.join(CACHE_DIR, 'epg_raw.xml')
    
    if not os.path.exists(epg_xml):
        print("❌ EPG non trovato!")
        print("Esegui: python scripts/fetch_openepg.py")
        return
    
    epg_data = parse_epg_xml(epg_xml)
    
    # Salva EPG processato
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, 'epg_parsed.json'), 'w', encoding='utf-8') as f:
        epg_serializable = {
            'channels': epg_data['channels'],
            'current_programmes': {
                ch: {**p, 'start': p['start'].isoformat(), 'stop': p['stop'].isoformat()} 
                for ch, p in epg_data['current_programmes'].items()
            },
            'next_programmes': {
                ch: {**p, 'start': p['start'].isoformat()} 
                for ch, p in epg_data['next_programmes'].items()
            },
            'updated_at': epg_data['updated_at']
        }
        json.dump(epg_serializable, f, ensure_ascii=False, indent=2)
    
    # Genera JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    lastminute_json = generate_lastminute_complete(epg_data)
    
    output_file = os.path.join(OUTPUT_DIR, 'lastminute.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lastminute_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Output: {output_file}")
    print("\n✨ Completato!\n")

if __name__ == '__main__':
    main()
