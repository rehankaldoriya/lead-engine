import tempfile,unittest
from pathlib import Path
from db import *
from scoring import score_lead,priority_for_score
from csv_tools import import_csv_bytes,import_preview,commit_import,export_csv
class CoreTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'t.sqlite3'; init_db(self.db)
 def tearDown(self): self.tmp.cleanup()
 def test_init_edit_persistence(self):
  lid=add_lead({'business_name':'Cafe Test','city':'Ahmedabad','score':55},self.db); self.assertEqual(get_lead(lid,self.db)['business_name'],'Cafe Test'); update_lead(lid,{'business_name':'Cafe Test','city':'Ahmedabad','phone':'+91 1234567890','score':60},self.db); self.assertEqual(get_lead(lid,self.db)['score'],60); self.assertEqual(len(list_leads(self.db)),1)
 def test_duplicates(self):
  add_lead({'business_name':'Cafe Test'},self.db)
  with self.assertRaises(ValueError): add_lead({'business_name':' cafe test '},self.db)
  self.assertIsNotNone(find_duplicate({'business_name':'CAFE TEST'},self.db))
 def test_missing_invalid(self):
  lid=add_lead({'business_name':'Minimal'},self.db); self.assertEqual(get_lead(lid,self.db)['email'],'')
  with self.assertRaises(ValueError): add_lead({'business_name':'Bad','website':'javascript:alert(1)'},self.db)
  with self.assertRaises(ValueError): add_lead({'business_name':'Bad','email':'not-email'},self.db)
 def test_scoring(self):
  score,_=score_lead({'premium_positioning':True,'ambience_presentation':True,'specialty_or_distinctive':True,'independent_boutique':None,'digital_opportunity':False,'expansion_potential':False}); self.assertEqual(score,60); self.assertEqual(priority_for_score(70),'High'); self.assertEqual(priority_for_score(45),'Medium'); self.assertEqual(priority_for_score(44),'Low')
 def test_csv_safe_merge(self):
  df=import_csv_bytes(b'business_name,city,phone,email\nCafe One,Ahmedabad,1111111111,\n,Ahmedabad,555,\n'); rows,errors=import_preview(df,{c:c for c in df.columns}); self.assertEqual((len(rows),len(errors)),(1,1)); self.assertEqual(commit_import(rows,self.db)['added'],1); self.assertIn('business_name',export_csv(list_leads(self.db)))
  df=import_csv_bytes(b'business_name,city,phone,email\nCafe One,Ahmedabad,2222222222,hi@example.com\n'); rows,_=import_preview(df,{c:c for c in df.columns}); result=commit_import(rows,self.db,'safe'); saved=get_lead(1,self.db); self.assertEqual(saved['phone'],'1111111111'); self.assertEqual(saved['email'],'hi@example.com'); self.assertEqual(result['updated'],1)
 def test_dashboard_offline_and_due(self):
  add_lead({'business_name':'Followup','next_followup_date':'2000-01-01','score':75},self.db); self.assertEqual(dashboard_stats(self.db)['Total leads'],1); self.assertEqual(len(due_followups(self.db)),1)
if __name__=='__main__': unittest.main()
