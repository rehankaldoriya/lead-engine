from pathlib import Path
from datetime import date
import os,json,shutil,tempfile,sqlite3
import pandas as pd
import streamlit as st
from db import *
from scoring import score_lead,priority_for_score,DEFAULT_WEIGHTS
from csv_tools import template_csv,export_csv,import_csv_bytes,import_preview,commit_import
from discovery import discover,DiscoveryError
from messaging import generate_message
st.set_page_config(page_title='ALOREX Lead Engine',page_icon='◈',layout='wide')
DB_PATH=Path(os.environ.get('ALOREX_LEAD_DB',str(DEFAULT_DB))); init_db(DB_PATH)
st.markdown('<style>.block-container{padding-top:1.4rem;max-width:1500px}[data-testid="stMetric"]{border:1px solid #e7e7e7;padding:12px 14px;border-radius:12px}</style>',unsafe_allow_html=True)
def tri_label(v): return 'Unknown' if v is None or v=='' else ('Yes' if int(v)==1 else 'No')
def tri_value(v): return None if v=='Unknown' else (1 if v=='Yes' else 0)
def lead_form(old=None,prefix='lead'):
    o=old or {}
    with st.form(prefix+'_form'):
        st.subheader('Business details'); a,b,c=st.columns(3)
        name=a.text_input('Business name *',o.get('business_name','')); catopts=['']+CATEGORIES; cityopts=['']+CITIES
        category=b.selectbox('Category',catopts,index=catopts.index(o.get('category','')) if o.get('category','') in catopts else 0)
        city=c.selectbox('City',cityopts,index=cityopts.index(o.get('city','')) if o.get('city','') in cityopts else 0)
        a,b,c=st.columns(3); neighbourhood=a.text_input('Neighbourhood',o.get('neighbourhood','')); address=b.text_input('Address',o.get('address','')); website=c.text_input('Website URL',o.get('website',''))
        a,b,c=st.columns(3); phone=a.text_input('Public business phone',o.get('phone','')); email=b.text_input('Public business email',o.get('email','')); instagram_url=c.text_input('Official Instagram URL',o.get('instagram_url',''))
        a,b,c=st.columns(3); menu_url=a.text_input('Public menu URL',o.get('menu_url','')); source_url=b.text_input('Source URL',o.get('source_url','')); source_name=c.text_input('Source name',o.get('source_name',''))
        social_links=st.text_area('Other official social links (one per line)',o.get('social_links',''))
        st.subheader('Qualification evidence'); labels={'premium_positioning':'Premium or luxury positioning','ambience_presentation':'Ambience / presentation focus','specialty_or_distinctive':'Specialty coffee / distinctive dining','independent_boutique':'Independent / boutique positioning','digital_opportunity':'Plausible digital experience opportunity','expansion_potential':'Multiple locations / expansion potential'}; ev={}; cols=st.columns(3)
        for i,(k,label) in enumerate(labels.items()):
            with cols[i%3]: ev[k]=tri_value(st.selectbox(label,['Unknown','Yes','No'],index=['Unknown','Yes','No'].index(tri_label(o.get(k))),key=f'{prefix}_{k}'))
        adjustment=st.number_input('Manual score adjustment (-100 to +100)',-100,100,int(o.get('manual_adjustment') or 0)); st.caption('Unknown evidence earns zero points. Scores are initial heuristics, not validated predictions.')
        st.subheader('Research checklist'); a,b,c=st.columns(3); research_premium=a.checkbox('Premium positioning reviewed',bool(o.get('research_premium') or 0)); research_digital_menu=b.checkbox('Digital menu checked',bool(o.get('research_digital_menu') or 0)); research_existing_qr=c.checkbox('Existing QR / ordering checked',bool(o.get('research_existing_qr') or 0))
        accuracy=st.selectbox('Contact detail accuracy',['Unknown','Yes','No'],index=['Unknown','Yes','No'].index(tri_label(o.get('research_contact_accuracy')))); research_opportunities=st.text_area('Potential improvements (evidence-based)',o.get('research_opportunities','')); research_notes=st.text_area('Research notes',o.get('research_notes',''))
        st.subheader('Sales pipeline'); a,b,c=st.columns(3); status=a.selectbox('Outreach status',STATUSES,index=STATUSES.index(o.get('outreach_status')) if o.get('outreach_status') in STATUSES else 0); last_contact=b.text_input('Last contact date (YYYY-MM-DD)',o.get('last_contact_date','')); next_followup=c.text_input('Next follow-up date (YYYY-MM-DD)',o.get('next_followup_date',''))
        a,b,c=st.columns(3); meeting=a.text_input('Meeting date (YYYY-MM-DD)',o.get('meeting_date','')); deal=c.text_input('Deal status / value',o.get('deal_status','')); response=b.text_input('Response notes',o.get('response_notes','')); discovery=st.text_input('Discovery date (YYYY-MM-DD)',o.get('discovery_date') or date.today().isoformat()); verified=st.text_input('Last verified date (YYYY-MM-DD)',o.get('last_verified_date',''))
        submitted=st.form_submit_button('Save lead',type='primary')
    if not submitted:return None
    score,breakdown=score_lead(ev,manual_adjustment=adjustment)
    return {'business_name':name,'category':category,'city':city,'neighbourhood':neighbourhood,'address':address,'website':website,'phone':phone,'email':email,'instagram_url':instagram_url,'social_links':social_links,'menu_url':menu_url,'source_url':source_url,'source_name':source_name,'discovery_date':discovery,'last_verified_date':verified,'research_notes':research_notes,'outreach_status':status,'last_contact_date':last_contact,'next_followup_date':next_followup,'meeting_date':meeting,'deal_status':deal,'response_notes':response,'manual_adjustment':adjustment,'score':score,'score_explanation':json.dumps(breakdown),**ev,'research_premium':int(research_premium),'research_digital_menu':int(research_digital_menu),'research_existing_qr':int(research_existing_qr),'research_contact_accuracy':tri_value(accuracy),'research_opportunities':research_opportunities}
st.title('◈ ALOREX Lead Engine'); st.caption('Local-first prospect research and sales pipeline · Ahmedabad & Gandhinagar')
with st.sidebar:
    st.markdown('### Navigation'); page=st.radio('Go to',['Dashboard','Leads & pipeline','Add lead','Business discovery','Import / export','Backups & settings']); st.divider(); st.caption(f'Database: `{DB_PATH}`'); st.caption('OSM coverage is incomplete; verify information before outreach.')
if page=='Dashboard':
    st.subheader('Filter dashboard')
    fa,fb,fc,fd,fe=st.columns(5)
    dcity=fa.selectbox('City',['All']+CITIES,key='dash_city')
    dcat=fb.selectbox('Category',['All']+CATEGORIES,key='dash_cat')
    dpriority=fc.selectbox('Priority',['All','High','Medium','Low'],key='dash_priority')
    dstatus=fd.selectbox('Status',['All']+STATUSES,key='dash_status')
    dmin=fe.slider('Minimum score',0,100,0,key='dash_score')
    rows=list_leads(DB_PATH,{'city':dcity,'category':dcat,'outreach_status':dstatus,'min_score':dmin})
    if dpriority!='All': rows=[r for r in rows if priority_for_score(int(r.get('score') or 0))==dpriority]
    today=date.today().isoformat()
    stats={'Total leads':len(rows),'Newly discovered':sum(r.get('discovery_date')==today for r in rows),'High priority':sum(int(r.get('score') or 0)>=70 for r in rows),'Qualified prospects':sum(r.get('outreach_status')=='Qualified' for r in rows),'Ready to contact':sum(r.get('outreach_status')=='Ready to Contact' for r in rows),'Leads contacted':sum(r.get('outreach_status') in ('Contacted','Replied','Meeting Scheduled','Proposal Sent','Won','Lost') for r in rows),'Replies received':sum(r.get('outreach_status')=='Replied' for r in rows),'Meetings scheduled':sum(r.get('outreach_status')=='Meeting Scheduled' for r in rows),'Deals won':sum(r.get('outreach_status')=='Won' for r in rows),'Follow-ups due':sum(r.get('next_followup_date')==today and r.get('outreach_status') not in ('Won','Lost','Not a Fit') for r in rows),'Overdue follow-ups':sum(bool(r.get('next_followup_date')) and r.get('next_followup_date')<today and r.get('outreach_status') not in ('Won','Lost','Not a Fit') for r in rows)}
    keys=list(stats)
    for i in range(0,len(keys),4):
        cols=st.columns(4)
        for col,k in zip(cols,keys[i:i+4]): col.metric(k,stats[k])
    st.subheader('Follow-ups needing attention')
    due=[r for r in rows if r.get('next_followup_date') and r.get('next_followup_date')<=today and r.get('outreach_status') not in ('Won','Lost','Not a Fit')]
    if due: st.dataframe(pd.DataFrame(due)[['id','business_name','city','outreach_status','next_followup_date','phone','email']],use_container_width=True,hide_index=True)
    else: st.success('No due or overdue follow-ups for these filters.')
    st.subheader('Highest-priority leads')
    if rows: st.dataframe(pd.DataFrame(rows[:10])[['id','business_name','city','category','score','outreach_status','next_followup_date']],use_container_width=True,hide_index=True)
    else: st.info('No leads match these filters. Add a lead or adjust filters.')
elif page=='Add lead':
    d=lead_form(prefix='new')
    if d:
        try: lid=add_lead(d,DB_PATH); st.success(f'Saved lead #{lid} · score {d["score"]} ({priority_for_score(d["score"])}).'); st.rerun()
        except Exception as e: st.error(str(e))
elif page=='Leads & pipeline':
    a,b,c,d=st.columns(4); search=a.text_input('Search'); city=b.selectbox('City',['All']+CITIES); cat=c.selectbox('Category',['All']+CATEGORIES); status=d.selectbox('Status',['All']+STATUSES); a,b=st.columns(2); lo=a.slider('Minimum score',0,100,0); hi=b.slider('Maximum score',lo,100,100)
    rows=list_leads(DB_PATH,{'search':search,'city':city,'category':cat,'outreach_status':status,'min_score':lo,'max_score':hi}); st.caption(f'{len(rows)} lead(s)')
    if rows:
        st.dataframe(pd.DataFrame(rows)[['id','business_name','city','category','score','outreach_status','next_followup_date','phone','email']],use_container_width=True,hide_index=True)
        opts={f"#{r['id']} · {r['business_name']}":r['id'] for r in rows}; selected=st.selectbox('Open lead profile',list(opts)); lid=opts[selected]; lead=get_lead(lid,DB_PATH); tabs=st.tabs(['Profile & edit','Outreach history','Draft message','Delete'])
        with tabs[0]:
            st.metric('Lead score',f"{lead['score']}/100",priority_for_score(lead['score'])); st.caption('Score rationale'); st.dataframe(pd.DataFrame(json.loads(lead.get('score_explanation') or '[]')),use_container_width=True,hide_index=True)
            for label,key in [('Website','website'),('Menu','menu_url'),('Instagram','instagram_url'),('Source','source_url')]:
                if lead.get(key): st.markdown(f'{label}: [{lead[key]}]({lead[key]})')
            st.write('Source name:',lead.get('source_name') or 'Not recorded'); edited=lead_form(lead,prefix=f'edit_{lid}')
            if edited:
                try: update_lead(lid,edited,DB_PATH); st.success('Lead updated.'); st.rerun()
                except Exception as e: st.error(str(e))
        with tabs[1]:
            with st.form(f'history_{lid}'):
                ch=st.selectbox('Channel',['WhatsApp','Instagram DM','Email','Phone','In-person','Other']); direction=st.selectbox('Event',['Contact sent','Reply received','Meeting','Note','Follow-up']); msg=st.text_area('Message / notes'); outcome=st.text_input('Outcome'); save=st.form_submit_button('Add history')
            if save: add_history(lid,ch,direction,msg,outcome,DB_PATH); st.success('History saved.'); st.rerun()
            history=get_history(lid,DB_PATH)
            if history: st.dataframe(pd.DataFrame(history),use_container_width=True,hide_index=True)
            else: st.info('No outreach history yet.')
        with tabs[2]:
            channel=st.selectbox('Channel',['WhatsApp','Instagram DM','Email'],key='msg_channel'); purpose=st.selectbox('Purpose',['Initial outreach','No-response follow-up','Follow-up after reply'],key='msg_purpose'); sender=st.text_input('Your sign-off (optional)'); draft=generate_message(lead,channel,purpose,sender); st.text_area('Draft — review/edit before sending',draft,height=220,key='draft_text'); st.caption('Draft only; nothing is sent automatically.')
            if st.button('Log draft in history'): add_history(lid,channel,'Draft created (not sent)',st.session_state.get('draft_text',draft),db_path=DB_PATH); st.success('Draft logged.')
        with tabs[3]:
            st.warning('Deleting also removes outreach history.'); confirm=st.checkbox('I understand and want to delete this lead.')
            if st.button('Delete lead permanently',disabled=not confirm): delete_lead(lid,DB_PATH); st.success('Deleted.'); st.rerun()
    else: st.info('No leads match these filters.')
elif page=='Business discovery':
    st.subheader('OpenStreetMap business discovery'); st.warning('OSM coverage is incomplete. Results are candidates, not verified classifications or sales-fit assessments.')
    with st.form('discovery_form'):
        city=st.selectbox('City',CITIES); cats=st.multiselect('Categories',CATEGORIES[:-1],default=['Cafés','Restaurants']); limit=st.slider('Maximum candidates',10,300,100,10); go=st.form_submit_button('Discover businesses')
    if go:
        if not cats: st.error('Choose at least one category.')
        else:
            with st.spinner('Querying OpenStreetMap Overpass…'):
                try: st.session_state['discovery_results']=discover(city,cats,limit); st.success(f"Found {len(st.session_state['discovery_results'])} named candidates.")
                except DiscoveryError as e: st.error(str(e))
                except Exception as e: st.error(f'Discovery error: {e}')
    candidates=st.session_state.get('discovery_results',[])
    if candidates:
        st.caption('Preview before saving. Public details are not independently verified.'); st.dataframe(pd.DataFrame(candidates).drop(columns=['verification_note'],errors='ignore'),use_container_width=True,hide_index=True); selected=st.multiselect('Select candidates to save',list(range(len(candidates))),default=list(range(len(candidates))),format_func=lambda i:f"{candidates[i]['business_name']} · {candidates[i]['category']}")
        if st.button('Save selected candidates'):
            added=skipped=0; errors=[]
            for i in selected:
                item={k:v for k,v in candidates[i].items() if k!='verification_note'}
                try: add_lead(item,DB_PATH); added+=1
                except ValueError as e:
                    if 'Possible duplicate' in str(e): skipped+=1
                    else: errors.append(f"{item['business_name']}: {e}")
                except Exception as e: errors.append(str(e))
            st.success(f'Saved {added}; skipped duplicates {skipped}; errors {len(errors)}.')
            if errors: st.write(errors)
elif page=='Import / export':
    st.subheader('CSV template'); st.download_button('Download CSV template',template_csv(),'alorex_lead_template.csv','text/csv'); st.subheader('Import CSV'); upload=st.file_uploader('Choose CSV',type=['csv'])
    if upload:
        try:
            df=import_csv_bytes(upload.getvalue()); st.write('Map source columns to lead fields; unmapped columns are ignored.'); mapping={}; cols=st.columns(3)
            for i,colname in enumerate(df.columns):
                with cols[i%3]:
                    target=st.selectbox(f'{colname} →',['Ignore']+LEAD_FIELDS,index=(['Ignore']+LEAD_FIELDS).index(colname) if colname in LEAD_FIELDS else 0,key=f'map_{colname}')
                    if target!='Ignore': mapping[colname]=target
            rows,errors=import_preview(df,mapping); st.caption(f'{len(rows)} valid row(s), {len(errors)} validation issue(s)')
            if errors: st.dataframe(pd.DataFrame(errors),use_container_width=True,hide_index=True)
            st.dataframe(pd.DataFrame([{**r['data'],'CSV row':r['row_number']} for r in rows]),use_container_width=True,hide_index=True); mode=st.radio('Duplicate handling',['safe','skip'],format_func=lambda x:'Safe update: fill blanks only' if x=='safe' else 'Skip duplicates')
            if st.button('Import valid rows',type='primary'):
                result=commit_import(rows,DB_PATH,mode); st.success(f"Added {result['added']}; updated {result['updated']}; skipped {result['skipped']}; errors {len(result['errors'])}.")
                if result['errors']: st.write(result['errors'])
        except Exception as e: st.error(str(e))
    st.subheader('Export'); city=st.selectbox('Export city',['All']+CITIES,key='excity'); status=st.selectbox('Export status',['All']+STATUSES,key='exstatus'); minscore=st.slider('Minimum score',0,100,0,key='exscore'); filtered=list_leads(DB_PATH,{'city':city,'outreach_status':status,'min_score':minscore}); st.download_button(f'Export {len(filtered)} filtered leads',export_csv(filtered),'alorex_leads_filtered.csv','text/csv'); st.download_button('Export all leads',export_csv(list_leads(DB_PATH)),'alorex_leads_all.csv','text/csv')
elif page=='Backups & settings':
    st.subheader('Database backup'); st.caption('Local SQLite file; not exposed as a public database endpoint.')
    if st.button('Prepare backup'): st.session_state['backup_bytes']=DB_PATH.read_bytes() if DB_PATH.exists() else b''
    if st.session_state.get('backup_bytes'): st.download_button('Download SQLite backup',st.session_state['backup_bytes'],f'alorex-backup-{date.today().isoformat()}.sqlite3','application/octet-stream')
    st.subheader('Restore backup'); st.warning('Restore replaces the current database. Download a backup first.'); restore=st.file_uploader('Choose backup file',type=['sqlite3','db','sqlite']); confirm=st.checkbox('I understand restore replaces my current database.')
    if restore and confirm and st.button('Restore database',type='primary'):
        temp=None
        try:
            with tempfile.NamedTemporaryFile(delete=False,suffix='.sqlite3') as f: f.write(restore.getvalue()); temp=Path(f.name)
            with sqlite3.connect(str(temp)) as check: tables={r[0] for r in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'leads','outreach_history'}.issubset(tables): raise ValueError('Not an ALOREX Lead Engine backup.')
            if DB_PATH.exists(): shutil.copy2(DB_PATH,DB_PATH.with_suffix(DB_PATH.suffix+'.pre-restore.bak'))
            shutil.copy2(temp,DB_PATH); init_db(DB_PATH); st.success('Restored. A pre-restore backup was saved beside the database.'); st.rerun()
        except Exception as e: st.error(f'Restore failed: {e}')
        finally:
            if temp and temp.exists(): temp.unlink()
    st.subheader('Scoring rules'); st.dataframe(pd.DataFrame([{'Factor':k.replace('_',' ').title(),'Maximum points':v} for k,v in DEFAULT_WEIGHTS.items()]),use_container_width=True,hide_index=True); st.caption('Weights live in scoring.py. Unknown evidence gets zero points; each lead supports a manual adjustment.')
