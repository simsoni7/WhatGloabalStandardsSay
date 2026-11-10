import sys,unittest,tempfile,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import backup_public_data as b

class PublicBackupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
  self.raw=b'\x89PNG\r\n\x1a\n'+b'fixed reviewed image bytes';self.fid='11111111-1111-4111-8111-111111111111'
  self.fields={'id':'contribution:screens:example','imageFileId':self.fid,'originalSha':b.sha(self.raw),'imagePath':'/api/wgss?resource=file&id='+self.fid}
  self.data={'items':[{'type':'screens','targetId':self.fields['id'],'revision':1,'patch':self.fields,'appliedVersions':[],'appliedAt':'2026-11-10T00:00:00Z'}],'providers':[]}
 def get(self,url):
  if 'resource=publications' in url:return b.encoded(self.data)
  if 'resource=recordVersions' in url:return b.encoded({'items':[{'revision':1,'fields':self.fields}]})
  if 'resource=file' in url:return self.raw
  raise AssertionError('unexpected endpoint')
 def test_complete_snapshot_verifies_and_unchanged_data_does_not_churn(self):
  first=b.backup(self.out,get=self.get);self.assertTrue(first['changed']);self.assertEqual(first['images'],1)
  before={p.name:p.read_bytes() for p in self.out.iterdir() if p.is_file()}
  second=b.backup(self.out,get=self.get);self.assertFalse(second['changed']);self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir() if p.is_file()})
 def test_corrupt_reviewed_image_prevents_publication(self):
  def get(url):return b'wrong bytes' if 'resource=file' in url else self.get(url)
  with self.assertRaisesRegex(ValueError,'hash_mismatch'):b.backup(self.out,get=get)
  self.assertFalse((self.out/'manifest.json').exists())
 def test_changed_source_during_export_keeps_previous_complete_snapshot(self):
  b.backup(self.out,get=self.get);previous=(self.out/'manifest.json').read_bytes();self.data['items'][0]['revision']=2;n=0
  def get(url):
   nonlocal n
   if 'resource=publications' in url:
    n+=1;data=copy.deepcopy(self.data)
    if n>1:data['items'][0]['revision']=3
    return b.encoded(data)
   return self.get(url)
  with self.assertRaisesRegex(ValueError,'source_changed'):b.backup(self.out,get=get)
  self.assertEqual(previous,(self.out/'manifest.json').read_bytes());b.verify(self.out)
 def test_missing_or_modified_asset_is_reported(self):
  b.backup(self.out,get=self.get);next((self.out/'assets').iterdir()).write_bytes(b'modified')
  with self.assertRaisesRegex(ValueError,'hash_mismatch'):b.verify(self.out)
 def test_failed_history_export_cannot_replace_a_complete_snapshot(self):
  b.backup(self.out,get=self.get);before=(self.out/'manifest.json').read_bytes()
  def get(url):
   if 'resource=recordVersions' in url:raise ValueError('unavailable')
   return self.get(url)
  with self.assertRaises(ValueError):b.backup(self.out,get=get)
  self.assertEqual(before,(self.out/'manifest.json').read_bytes())

if __name__=='__main__':unittest.main()
