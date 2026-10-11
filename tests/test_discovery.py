import unittest,requests
from unittest.mock import Mock
from discovery import build_query,discover,DiscoveryError
class DiscoveryTests(unittest.TestCase):
 def test_query_validation(self):
  self.assertIn('out center;',build_query('Ahmedabad',['Cafés','Restaurants'],50))
  with self.assertRaises(ValueError): build_query('Other',['Cafés'])
 def test_network_failure(self):
  fake=Mock(); fake.post.side_effect=requests.Timeout('timed out')
  with self.assertRaises(DiscoveryError): discover('Ahmedabad',['Cafés'],session=fake)
 def test_osm_payload(self):
  fake=Mock(); response=Mock(); response.json.return_value={'elements':[{'type':'node','id':1,'lat':23,'lon':72,'tags':{'name':'Test Cafe','amenity':'cafe','phone':'1234567890','website':'https://example.com'}}]}; response.raise_for_status.return_value=None; fake.post.return_value=response
  result=discover('Ahmedabad',['Cafés'],session=fake); self.assertEqual(result[0]['business_name'],'Test Cafe'); self.assertEqual(result[0]['source_name'],'OpenStreetMap / Overpass API')
if __name__=='__main__': unittest.main()
