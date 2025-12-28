#!/usr/bin/env python3
"""
Last Minute BASE - Solo EPG

"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

CACHE_DIR = 'cache'
OUTPUT_DIR = 'output'

def parse_epg_xml(xml_file: str):
    """Parse EPG XML"""
    
    print(f" Parsing {xml_file}...")
    
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
    
    print(f" Trovati {len(all_channels)} canali")
    
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
                
                current_programmes[channel_id] = {
                    'start': start,
                    'stop': stop,
                    'start_str': start.strftime('%H:%M'),
                    'stop_str': stop.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None else 'In onda',
                    'desc': desc_elem.text if desc_elem is not None else ''
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
    
    print(f" {len(current_programmes)} canali con programmi in onda")
    
    return {
        'channels': all_channels,
        'current_programmes': current_programmes,
        'next_programmes': next_programmes
    }

def generate_lastminute_base(epg_data):
    """Genera JSON semplice - solo EPG"""
    
    print("\n Generazione Last Minute BASE...")
    
    mandrakodi = {
        "SetViewMode": "51",
        "RefreshList": "10800",
        "items": []
    }
    
    # Header semplice
    now = datetime.now()
    mandrakodi['items'].append({
        "title": "Last Minute - EPG",
        "link": "ignoreme",
        "info": f"Aggiornato: {now.strftime('%d/%m/%Y %H:%M')}"
    })
    
    # Canali in ordine alfabetico
    channels_list = list(epg_data['channels'].items())
    channels_list.sort(key=lambda x: x[1]['name'])
    
    for channel_id, channel_info in channels_list:
        current_prog = epg_data['current_programmes'].get(channel_id)
        next_prog = epg_data['next_programmes'].get(channel_id)
        
        if not current_prog:
            continue
        
        # Titolo: Nome canale - Orario Programma
        title = f"{channel_info['name']} - {current_prog['start_str']} {current_prog['title']}"
        
        # Info: orario + descrizione + prossimo
        info_parts = [
            f"In onda: {current_prog['start_str']} - {current_prog['stop_str']}"
        ]
        
        if current_prog['desc']:
            info_parts.append(f"\n{current_prog['desc']}")
        
        if next_prog:
            info_parts.append(f"\nA seguire ({next_prog['start_str']}): {next_prog['title']}")
        
        item = {
            "title": title,
            "link": "ignoreme",
            "info": '\n'.join(info_parts)
        }
        
        # Aggiungi icona se disponibile
        if channel_info.get('icon'):
            item["thumbnail"] = channel_info['icon']
        
        mandrakodi['items'].append(item)
    
    print(f" Generati {len(mandrakodi['items'])} items")
    
    return mandrakodi

def main():
    """Main"""
    
    print(" Last Minute BASE - Solo EPG\n")
    
    epg_xml = os.path.join(CACHE_DIR, 'epg_raw.xml')
    
    if not os.path.exists(epg_xml):
        print(" EPG non trovato!")
        return
    
    epg_data = parse_epg_xml(epg_xml)
    
    # Genera JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    lastminute_json = generate_lastminute_base(epg_data)
    
    output_file = os.path.join(OUTPUT_DIR, 'lastminute.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lastminute_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n Output: {output_file}")
    print(" Completato!\n")

if __name__ == '__main__':
    main()
