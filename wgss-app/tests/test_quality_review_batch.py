import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import quality_review_batch as q
class QualityTests(unittest.TestCase):
 def test_forged_or_incomplete_model_coverage_is_rejected(self):
  rows=[{'key':'a'},{'key':'b'}]
  for raw in [{'rows':[{'key':'a'},{'key':'a'}]},{'rows':[{'key':'a'}]}]:
   with self.assertRaises(ValueError):q.covered_rows(raw,rows)
 def test_only_unambiguous_independent_checks_pass(self):
  row={k:True for k in ['pairAccurate','koreanAccurate','financeRelevant','privacyClear','readable']};row.update(decision='approve',confidence=.99)
  self.assertTrue(q.approve_decision(row))
  for key,value in [('confidence',.94),('confidence',True),('pairAccurate','true'),('koreanAccurate',False),('decision','hold')]:self.assertFalse(q.approve_decision({**row,key:value}))
 def test_korean_original_is_reused_without_model_rewriting(self):
  item={'key':'ja:BHD','sourceKorean':{'korean':'바레인 디나르'},'payload':{}}
  model=Mock();q.complete_korean([item],model)
  self.assertEqual(item['korean'],'바레인 디나르');self.assertEqual(item['koreanBasis'],'source_korean_reused');model.call.assert_not_called()
 def test_draft_is_explicitly_labelled_ai_and_original_pair_not_changed(self):
  item={'key':'fr:Payment','sourceKorean':None,'koreanCandidates':[],'payload':{'english':'Payment','target':'Paiement','language':'fr'}}
  model=Mock();model.call.return_value={'rows':[{'key':'fr:Payment','korean':'지급'}]}
  q.complete_korean([item],model);self.assertEqual(item['koreanBasis'],'ai_quality_reviewed');self.assertEqual(item['payload']['target'],'Paiement')
 def test_changed_source_bytes_never_reach_model(self):
  with tempfile.TemporaryDirectory() as directory:
   agent=object.__new__(q.SourceSearchAgent);agent.cache=Path(directory)
   with patch.object(q,'fetch_bytes',return_value=b'changed'):
    with self.assertRaises(ValueError):agent.read('https://raw.githubusercontent.com/a/b',expected='a'*64)
 def test_currency_search_extracts_the_code_name_only(self):
  with tempfile.TemporaryDirectory() as directory:
   agent=object.__new__(q.SourceSearchAgent);agent.cache=Path(directory)
   raw='<table><tr><td>BND</td><td>브루나이(달러)</td><td>1234.56</td></tr></table>'.encode()
   with patch.object(q,'fetch_bytes',return_value=raw):result=agent.currency_name_search('BND')
   self.assertEqual(result['korean'],'브루나이 달러');self.assertNotIn('1234',str(result));self.assertEqual(result['sha256'],q.digest(raw))
 def test_signed_request_replays_cannot_redirect_credentials(self):
  opener=MagicMock();opener.open.return_value.__enter__.return_value.read.return_value=b'{"ok":true}'
  with patch.object(q.urllib.request,'build_opener',return_value=opener),patch.object(q.time,'time',return_value=1700000000):q.signed_api('https://example.com/api/wgss','secret',{'action':'test','korean':'바레인 디나르'})
  request=opener.open.call_args.args[0];message='\n'.join(['wgss-quality-v1','1700000000','POST','/api/wgss',request.data.decode()]);expected=q.hmac.new(b'secret',message.encode(),q.hashlib.sha256).hexdigest()
  self.assertEqual(request.get_header('X-wgss-automation-signature'),expected)
  self.assertNotEqual(expected,q.hmac.new(b'secret',(message+'changed').encode(),q.hashlib.sha256).hexdigest())
if __name__=='__main__':unittest.main()
