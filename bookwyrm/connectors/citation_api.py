#!/usr/bin/env python3

# Python client for Thinkst Citation
# (C) 2023 Thinkst Applied Research
# Author: Jacob Torrey

from typing import List, Dict, Union
from supabase import create_client, Client
import json

CITATION_URL = 'https://ujmzkvtptrvgtlcamyii.supabase.co'
CITATION_ACCESS_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqbXprdnRwdHJ2Z3RsY2FteWlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NjM2OTg5OTMsImV4cCI6MTk3OTI3NDk5M30.Xwy8CLPq3G0aCO3gMnv_bz_FUe8UfhOHch93xutAm5w'

client = create_client(CITATION_URL, CITATION_ACCESS_KEY)

def get_by_id(id : int, table : str, select : str, raw : bool) -> Union[Dict, str]:
    data = client.table(table).select(select).eq('id', str(id)).execute()
    if len(data.data) == 0:
        if raw:
            return []
        return json.dumps([])
    if raw:
        return data.data
    return json.dumps(data.data)

def get_talk(id : int, raw : bool = True) -> Union[Dict, str]:
    raw_data = get_by_id(id, 'talks', '*,speakers(*),conferences(conference_name,edition,date_from,date_to)', raw)[0]
    cleaned = {
        'id': raw_data.get('id'),
        'citation_id': str(raw_data.get('id')),
        'title': raw_data.get('title'),
        'url': raw_data.get('link'),
        'summary': raw_data.get('summary'),
        'authors': [],
        'venue': '',
        'date': ''
    }
    if raw_data.get('conferences'):
        cleaned['venue'] = raw_data['conferences'].get('conference_name') + ' ' + raw_data['conferences'].get('edition')
        if raw_data['conferences'].get('date_from'):
            cleaned['date'] = raw_data['conferences'].get('date_from')
        if raw_data['conferences'].get('date_to'):
            cleaned['date'] = raw_data['conferences'].get('date_to')
    for a in raw_data.get('speakers', []):
        cleaned['authors'].append({'id': a.get('id'), 'name': a.get('first_name', '') + ' ' + a.get('surname', '')})
    return cleaned

def get_author(id : int, raw : bool = True) -> Union[Dict, str]:
    return get_by_id(id, 'speakers', '*,talks(*)', raw)

def search(q : str, limit : int = 5, raw : bool = True) -> Union[Dict, str]:
    '''Search both talk titles and author names for the passed query, returning a prioritized JSON string of results'''
    def _search_helper(q : str, limit : int, rpc : str) -> List[Dict]:
        q = client.rpc(rpc, {'keyword': q})
        q.params = {'limit': limit}
        return q.execute().data
    talks = _search_helper(q, limit, 'search_talks')
    authors = _search_helper(q, limit, 'search_speakers')
    out = []
    for t in talks:
        res = {
            'title': t.get('title'),
            'id': t.get('id'),
            'summary': t.get('summary'),
            'authors': []   
            }
        if len(t.get('conferences')) > 0:
            res['venue'] = t.get('conferences').get('conference_name')
        for a in t.get('speakers'):
            res['authors'].append({'id': a.get('id'), 'name': a.get('first_name') + ' ' + a.get('surname')})
        out.append(res)
    for a in authors:
        works = get_author(a.get('id'), raw=True)
        for w in works:
            res = {
                'title': w.get('title'),
                'id': w.get('id'),
                'summary': w.get('summary'),
                'authors': [{'id': a.get('id'), 'name': a.get('first_name') + ' ' + a.get('surname')}]   
            }
            out.append(res)
    if raw:
        return out[:limit]
    return json.dumps(out[:limit])
