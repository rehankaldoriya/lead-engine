"""OpenStreetMap Overpass discovery. Results are candidates requiring verification."""
import requests
from datetime import date
OVERPASS_URL='https://overpass-api.de/api/interpreter'
AREAS={'Ahmedabad':'area["name"="Ahmedabad"]["boundary"="administrative"]','Gandhinagar':'area["name"="Gandhinagar"]["boundary"="administrative"]'}
TAGS={'Cafés':['["amenity"="cafe"]'],'Specialty coffee shops':['["shop"="coffee"]','["cuisine"~"coffee",i]'],'Restaurants':['["amenity"="restaurant"]'],'Fine dining':['["amenity"="restaurant"]'],'Bakeries and patisseries':['["shop"="bakery"]'],'Boutique dining':['["amenity"="restaurant"]','["amenity"="cafe"]']}
class DiscoveryError(RuntimeError): pass
def build_query(city,categories,limit=100):
    if city not in AREAS: raise ValueError('Choose Ahmedabad or Gandhinagar.')
    limit=max(1,min(500,int(limit))); tags=list(dict.fromkeys(t for cat in categories for t in TAGS.get(cat,[])))
    if not tags: raise ValueError('Select at least one supported category.')
    return '[out:json][timeout:25];\n'+AREAS[city]+'->.searchArea;\n(\n'+'\n'.join('nwr'+t+'(area.searchArea);' for t in tags)+'\n);\nout center;'
def category_for(tags):
    if tags.get('shop')=='bakery': return 'Bakeries and patisseries'
    if tags.get('shop')=='coffee' or 'coffee' in tags.get('cuisine','').lower(): return 'Specialty coffee shops'
    if tags.get('amenity')=='cafe': return 'Cafés'
    if tags.get('amenity')=='restaurant': return 'Restaurants'
    return 'Other'
def discover(city,categories,limit=100,timeout=35,session=None):
    query=build_query(city,categories,limit); client=session or requests
    try:
        response=client.post(OVERPASS_URL,data={'data':query},timeout=(5,timeout),headers={'User-Agent':'AlorexLeadEngine/1.0 (local prospect research tool)'}); response.raise_for_status(); payload=response.json()
    except requests.RequestException as e: raise DiscoveryError(f'OpenStreetMap discovery request failed: {e}') from e
    except ValueError as e: raise DiscoveryError('The discovery service returned an unreadable response.') from e
    out=[]
    for el in payload.get('elements',[]):
        tags=el.get('tags',{}); name=tags.get('name','').strip()
        if not name: continue
        parts=[tags.get(k,'') for k in ('addr:housenumber','addr:street','addr:suburb','addr:city')]; typ=el.get('type','node'); oid=el.get('id'); insta=tags.get('contact:instagram') or tags.get('instagram') or ''
        if insta and not insta.startswith('http'): insta='https://www.instagram.com/'+insta.strip('@/')
        out.append({'business_name':name,'category':category_for(tags),'city':city,'neighbourhood':tags.get('addr:suburb') or tags.get('addr:neighbourhood') or '','address':', '.join(x for x in parts if x),'website':tags.get('contact:website') or tags.get('website') or '','phone':tags.get('contact:phone') or tags.get('phone') or '','email':tags.get('contact:email') or tags.get('email') or '','instagram_url':insta,'source_url':f'https://www.openstreetmap.org/{typ}/{oid}','source_name':'OpenStreetMap / Overpass API','discovery_date':date.today().isoformat(),'outreach_status':'New','verification_note':'OSM candidate; contact details and venue fit require verification.'})
    seen=set(); unique=[]
    for item in out:
        key=(item['business_name'].casefold(),item['address'].casefold())
        if key not in seen: seen.add(key); unique.append(item)
    return unique[:max(1,min(500,int(limit)))]
