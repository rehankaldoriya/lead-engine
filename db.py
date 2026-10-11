"""SQLite persistence, validation and pipeline queries."""
import sqlite3, re
from pathlib import Path
from datetime import date, datetime
DEFAULT_DB=Path(__file__).resolve().parent/'data'/'alorex_leads.sqlite3'
STATUSES=['New','Researching','Qualified','Ready to Contact','Contacted','Replied','Meeting Scheduled','Proposal Sent','Won','Lost','Not a Fit']
CATEGORIES=['Cafés','Specialty coffee shops','Restaurants','Fine dining','Bakeries and patisseries','Boutique dining','Other']
CITIES=['Ahmedabad','Gandhinagar']
BOOL_FIELDS={'premium_positioning','ambience_presentation','specialty_or_distinctive','independent_boutique','digital_opportunity','expansion_potential','research_premium','research_digital_menu','research_existing_qr','research_contact_accuracy'}
DATE_FIELDS={'discovery_date','last_verified_date','last_contact_date','next_followup_date','meeting_date'}
URL_FIELDS={'website','instagram_url','menu_url','source_url'}
LEAD_FIELDS=['business_name','category','city','neighbourhood','address','website','phone','email','instagram_url','social_links','menu_url','source_url','source_name','discovery_date','last_verified_date','score','score_explanation','research_notes','outreach_status','last_contact_date','next_followup_date','response_notes','meeting_date','deal_status','manual_adjustment','premium_positioning','ambience_presentation','specialty_or_distinctive','independent_boutique','digital_opportunity','expansion_potential','research_premium','research_digital_menu','research_existing_qr','research_opportunities','research_contact_accuracy']
class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb):
        try: return super().__exit__(exc_type, exc, tb)
        finally: self.close()
def connect(db_path=DEFAULT_DB):
    p=Path(db_path); p.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(str(p),timeout=10,factory=ClosingConnection); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA busy_timeout=10000'); return c
def init_db(db_path=DEFAULT_DB):
    with connect(db_path) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT,business_name TEXT NOT NULL,category TEXT DEFAULT '',city TEXT DEFAULT '',neighbourhood TEXT DEFAULT '',address TEXT DEFAULT '',website TEXT DEFAULT '',phone TEXT DEFAULT '',email TEXT DEFAULT '',instagram_url TEXT DEFAULT '',social_links TEXT DEFAULT '',menu_url TEXT DEFAULT '',source_url TEXT DEFAULT '',source_name TEXT DEFAULT '',discovery_date TEXT DEFAULT '',last_verified_date TEXT DEFAULT '',score INTEGER DEFAULT 0 CHECK(score BETWEEN 0 AND 100),score_explanation TEXT DEFAULT '',research_notes TEXT DEFAULT '',outreach_status TEXT DEFAULT 'New',last_contact_date TEXT DEFAULT '',next_followup_date TEXT DEFAULT '',response_notes TEXT DEFAULT '',meeting_date TEXT DEFAULT '',deal_status TEXT DEFAULT '',manual_adjustment INTEGER DEFAULT 0,premium_positioning INTEGER,ambience_presentation INTEGER,specialty_or_distinctive INTEGER,independent_boutique INTEGER,digital_opportunity INTEGER,expansion_potential INTEGER,research_premium INTEGER,research_digital_menu INTEGER,research_existing_qr INTEGER,research_opportunities TEXT DEFAULT '',research_contact_accuracy INTEGER,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outreach_history(id INTEGER PRIMARY KEY AUTOINCREMENT,lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,channel TEXT NOT NULL DEFAULT '',direction TEXT NOT NULL DEFAULT 'Note',message TEXT DEFAULT '',event_date TEXT NOT NULL,outcome TEXT DEFAULT '');
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(outreach_status); CREATE INDEX IF NOT EXISTS idx_leads_city ON leads(city); CREATE INDEX IF NOT EXISTS idx_leads_name ON leads(business_name);
        """); c.commit()
def norm(v): return '' if v is None else str(v).strip()
def validate(d):
    if not norm(d.get('business_name')): raise ValueError('Business name is required.')
    city=norm(d.get('city'))
    if city and city not in CITIES: raise ValueError('City must be Ahmedabad or Gandhinagar (or blank).')
    status=norm(d.get('outreach_status')) or 'New'
    if status not in STATUSES: raise ValueError('Invalid outreach status.')
    for f in URL_FIELDS:
        v=norm(d.get(f))
        if v and not re.match(r'^https?://',v,re.I): raise ValueError(f'{f} must start with http:// or https://.')
    email=norm(d.get('email'))
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email): raise ValueError('Email format appears invalid.')
    for f in DATE_FIELDS:
        v=norm(d.get(f))
        if v:
            try: date.fromisoformat(v[:10])
            except ValueError: raise ValueError(f'{f} must use YYYY-MM-DD.')
def _prepare(d):
    out={}
    for f in LEAD_FIELDS:
        v=d.get(f)
        if f in BOOL_FIELDS:
            if v is None or v=='' or str(v).lower()=='unknown': out[f]=None
            elif isinstance(v,str): out[f]=1 if v.strip().lower() in ('true','yes','1','y') else 0
            else: out[f]=1 if v is True or v==1 else 0
        elif f in ('score','manual_adjustment'):
            try: out[f]=max(0,min(100,int(v or 0))) if f=='score' else max(-100,min(100,int(v or 0)))
            except (TypeError,ValueError): out[f]=0
        else: out[f]=norm(v)
    return out
def find_duplicate(d,db_path=DEFAULT_DB,exclude_id=None):
    name=norm(d.get('business_name')).casefold(); website=norm(d.get('website')).rstrip('/').casefold(); phone=re.sub(r'\D','',norm(d.get('phone')))
    with connect(db_path) as c: rows=c.execute('SELECT id,business_name,website,phone FROM leads').fetchall()
    for r in rows:
        if exclude_id is not None and r['id']==int(exclude_id): continue
        if name and r['business_name'].strip().casefold()==name: return dict(r)
        if website and r['website'].rstrip('/').casefold()==website: return dict(r)
        other=re.sub(r'\D','',r['phone'] or '')
        if phone and len(phone)>=8 and phone==other: return dict(r)
    return None
def add_lead(d,db_path=DEFAULT_DB,allow_duplicate=False):
    validate(d); dup=find_duplicate(d,db_path)
    if dup and not allow_duplicate: raise ValueError(f"Possible duplicate of lead #{dup['id']}: {dup['business_name']}")
    v=_prepare(d); now=datetime.now().isoformat(timespec='seconds'); v.update(created_at=now,updated_at=now); cols=list(v)
    with connect(db_path) as c:
        cur=c.execute(f"INSERT INTO leads ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",list(v.values())); c.commit(); return cur.lastrowid
def update_lead(lead_id,d,db_path=DEFAULT_DB):
    validate(d); dup=find_duplicate(d,db_path,exclude_id=lead_id)
    if dup: raise ValueError(f"Possible duplicate of lead #{dup['id']}: {dup['business_name']}")
    v=_prepare(d); v['updated_at']=datetime.now().isoformat(timespec='seconds')
    with connect(db_path) as c:
        cur=c.execute('UPDATE leads SET '+','.join(f'{k}=?' for k in v)+' WHERE id=?',list(v.values())+[int(lead_id)])
        if not cur.rowcount: raise ValueError('Lead not found.')
        c.commit()
def get_lead(lead_id,db_path=DEFAULT_DB):
    with connect(db_path) as c: row=c.execute('SELECT * FROM leads WHERE id=?',(int(lead_id),)).fetchone()
    return dict(row) if row else None
def list_leads(db_path=DEFAULT_DB,filters=None):
    f=filters or {}; clauses=[]; params=[]
    for k in ('city','category','outreach_status'):
        v=f.get(k)
        if v and v!='All': clauses.append(f'{k}=?'); params.append(v)
    for k,op in (('min_score','>='),('max_score','<=')):
        if f.get(k) is not None: clauses.append(f'score{op}?'); params.append(int(f[k]))
    if f.get('search'):
        clauses.append('(business_name LIKE ? OR neighbourhood LIKE ? OR address LIKE ? OR phone LIKE ? OR email LIKE ?)'); params+=['%'+str(f['search']).strip()+'%']*5
    sql='SELECT * FROM leads'+(' WHERE '+' AND '.join(clauses) if clauses else '')+' ORDER BY score DESC,business_name COLLATE NOCASE'
    with connect(db_path) as c: return [dict(r) for r in c.execute(sql,params).fetchall()]
def delete_lead(lead_id,db_path=DEFAULT_DB):
    with connect(db_path) as c: c.execute('DELETE FROM leads WHERE id=?',(int(lead_id),)); c.commit()
def add_history(lead_id,channel,direction,message,outcome='',db_path=DEFAULT_DB):
    with connect(db_path) as c: c.execute('INSERT INTO outreach_history(lead_id,channel,direction,message,event_date,outcome) VALUES(?,?,?,?,?,?)',(int(lead_id),norm(channel),norm(direction),norm(message),datetime.now().isoformat(timespec='seconds'),norm(outcome))); c.commit()
def get_history(lead_id,db_path=DEFAULT_DB):
    with connect(db_path) as c: return [dict(r) for r in c.execute('SELECT * FROM outreach_history WHERE lead_id=? ORDER BY id DESC',(int(lead_id),)).fetchall()]
def due_followups(db_path=DEFAULT_DB,today=None):
    today=today or date.today().isoformat()
    with connect(db_path) as c: return [dict(r) for r in c.execute("SELECT * FROM leads WHERE next_followup_date<>'' AND next_followup_date<=? AND outreach_status NOT IN ('Won','Lost','Not a Fit') ORDER BY next_followup_date",(today,)).fetchall()]
def dashboard_stats(db_path=DEFAULT_DB):
    today=date.today().isoformat()
    with connect(db_path) as c:
        q=lambda sql,args=(): c.execute(sql,args).fetchone()[0]
        return {'Total leads':q('SELECT COUNT(*) FROM leads'),'Newly discovered':q('SELECT COUNT(*) FROM leads WHERE discovery_date=?',(today,)),'High priority':q('SELECT COUNT(*) FROM leads WHERE score>=70'),'Qualified prospects':q("SELECT COUNT(*) FROM leads WHERE outreach_status='Qualified'"),'Ready to contact':q("SELECT COUNT(*) FROM leads WHERE outreach_status='Ready to Contact'"),'Leads contacted':q("SELECT COUNT(*) FROM leads WHERE outreach_status IN ('Contacted','Replied','Meeting Scheduled','Proposal Sent','Won','Lost')"),'Replies received':q("SELECT COUNT(*) FROM leads WHERE outreach_status='Replied'"),'Meetings scheduled':q("SELECT COUNT(*) FROM leads WHERE outreach_status='Meeting Scheduled'"),'Deals won':q("SELECT COUNT(*) FROM leads WHERE outreach_status='Won'"),'Follow-ups due':q("SELECT COUNT(*) FROM leads WHERE next_followup_date=? AND outreach_status NOT IN ('Won','Lost','Not a Fit')",(today,)),'Overdue follow-ups':q("SELECT COUNT(*) FROM leads WHERE next_followup_date<>'' AND next_followup_date<? AND outreach_status NOT IN ('Won','Lost','Not a Fit')",(today,))}
def merge_safe(existing,incoming):
    merged=dict(existing); changed=[]
    for k,v in incoming.items():
        if k in ('id','created_at','updated_at') or v is None or str(v).strip()=='': continue
        if merged.get(k) is None or str(merged.get(k)).strip()=='': merged[k]=v; changed.append(k)
    return merged,changed
