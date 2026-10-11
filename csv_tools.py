import io
import pandas as pd
from db import LEAD_FIELDS,add_lead,find_duplicate,get_lead,update_lead,merge_safe
TEMPLATE_COLUMNS=['business_name','category','city','neighbourhood','address','website','phone','email','instagram_url','social_links','menu_url','source_url','source_name','discovery_date','last_verified_date','research_notes','outreach_status']
def template_csv(): return ','.join(TEMPLATE_COLUMNS)+'\n'
def export_csv(rows):
    df=pd.DataFrame(rows); cols=['id']+LEAD_FIELDS; return df.reindex(columns=[c for c in cols if c in df.columns]).to_csv(index=False)
def import_csv_bytes(raw):
    try: return pd.read_csv(io.BytesIO(raw),dtype=str,keep_default_na=False)
    except Exception as e: raise ValueError(f'Could not read CSV: {e}') from e
def import_preview(df,mapping=None):
    mapping=mapping or {c:c for c in df.columns if c in LEAD_FIELDS}; rows=[]; errors=[]
    for idx,raw in df.iterrows():
        item={mapping[src]:str(raw[src]).strip() for src in mapping if src in df.columns and mapping[src] in LEAD_FIELDS}
        if not item.get('business_name','').strip(): errors.append({'row':int(idx)+2,'error':'Business name is required'})
        else: rows.append({'row_number':int(idx)+2,'data':item})
    return rows,errors
def commit_import(rows,db_path,mode='safe'):
    out={'added':0,'updated':0,'skipped':0,'errors':[]}
    for row in rows:
        d=row['data']
        try:
            dup=find_duplicate(d,db_path)
            if not dup: add_lead(d,db_path); out['added']+=1
            elif mode=='safe':
                old=get_lead(dup['id'],db_path); merged,changed=merge_safe(old,d)
                if changed: update_lead(dup['id'],merged,db_path); out['updated']+=1
                else: out['skipped']+=1
            else: out['skipped']+=1
        except Exception as e: out['errors'].append(f"Row {row.get('row_number','?')}: {e}")
    return out
