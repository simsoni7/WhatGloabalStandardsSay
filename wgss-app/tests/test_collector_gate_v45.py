import sys,unittest,copy,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collector_action_gate_v45 import *
class GateTests(unittest.TestCase):
 def setUp(self):
  self.href='https://bank.example/product-details';self.control={'tag':'A','href':self.href,'text':'View account details'}
  self.s={'source_html':'<main><a href="'+self.href+'">View account details</a><p>Read product features.</p></main>','source_url':'https://bank.example/accounts','view_text':'View account details. Read product features.','control':self.control,'op':'goto','candidate_kind':'anchor_navigation','official':True}
  self.c={'href':self.href,'op':'goto','candidate_kind':'anchor_navigation','control':self.control};self.d=make_review_decision(self.s,'worker B','Original source/control and visible surrounding copy inspected; readonly details anchor.')
 def test_safe_navigation_both_gates_and_queue_callback(self):
  self.assertTrue(queue_gate(self.c,self.s,self.d));self.assertTrue(execution_gate(self.c,self.s,self.d));q=ReviewedActionQueue();q.enqueue(self.c,self.s,self.d);calls=[];q.execute_next(self.s,calls.append);self.assertEqual(calls,[{'op':'goto','href':self.href}])
 def test_unreviewed_boolean_decision_denied_both(self):
  for d in [None,True,{'approved':True}]:
   for gate in [queue_gate,execution_gate]:
    with self.subTest(d=d,gate=gate.__name__),self.assertRaises(GateDenied):gate(self.c,self.s,d)
 def test_wells_information_sharing_denied_review_queue_execution(self):
  s=copy.deepcopy(self.s);s['view_text']="By selecting Let’s go or Sign on: You authorize your wireless carrier to use or disclose information about your account and wireless device."
  with self.assertRaisesRegex(GateDenied,'consent_boundary'):make_review_decision(s,'B','reviewed')
  for gate in [queue_gate,execution_gate]:
   with self.assertRaisesRegex(GateDenied,'consent_boundary'):gate(self.c,s,self.d)
 def test_natwest_carry_on_documents_and_estatements_denied(self):
  s=copy.deepcopy(self.s);s['view_text']="If you carry on applying, it means you're happy with what's in these documents. And happy to view your statements in Online Banking - not posted."
  for gate in [queue_gate,execution_gate]:
   with self.assertRaisesRegex(GateDenied,'consent_boundary'):gate(self.c,s,self.d)
 def test_changed_source_view_control_href_blocked_both(self):
  for key,value in [('source_html',self.s['source_html']+'<p>new</p>'),('view_text','New unrelated context'),('source_url','https://bank.example/new')]:
   s=copy.deepcopy(self.s);s[key]=value
   for gate in [queue_gate,execution_gate]:
    with self.subTest(key=key,gate=gate.__name__),self.assertRaises(GateDenied):gate(self.c,s,self.d)
  for key,value in [('href','https://bank.example/changed'),('text','Changed copy'),('tag','BUTTON')]:
   s=copy.deepcopy(self.s);s['control'][key]=value
   for gate in [queue_gate,execution_gate]:
    with self.subTest(key=key,gate=gate.__name__),self.assertRaises(GateDenied):gate(self.c,s,self.d)
 def test_changed_candidate_and_forged_hash(self):
  c=copy.deepcopy(self.c);c['href']='https://bank.example/different'
  for gate in [queue_gate,execution_gate]:
   with self.assertRaises(GateDenied):gate(c,self.s,self.d)
   s=copy.deepcopy(self.s);s['source_sha256']='0'*64
   with self.assertRaisesRegex(GateDenied,'forged_declared_source_hash'):gate(self.c,s,self.d)
 def test_no_input_submit_auth_button_or_nonofficial_paths(self):
  for op in ['fill','type','submit','login','auth','click']:
   s=copy.deepcopy(self.s);s['op']=op
   with self.subTest(op=op),self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
  for key,value in [('official',False),('view_text',''),('candidate_kind','model_approved')]:
   s=copy.deepcopy(self.s);s[key]=value
   with self.subTest(key=key),self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
  s=copy.deepcopy(self.s);s['control']['tag']='INPUT'
  with self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
 def test_token_and_unobserved_href_denied(self):
  for href in ['http://bank.example/a','https://bank.example/a?token=secret','https://bank.example/unobserved']:
   s=copy.deepcopy(self.s);s['control']['href']=href
   with self.subTest(href=href),self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
 def test_execution_change_never_calls_callback_and_logs_boundary(self):
  q=ReviewedActionQueue();q.enqueue(self.c,self.s,self.d);s=copy.deepcopy(self.s);s['view_text']='You authorize wireless carrier data disclosure.';calls=[]
  with self.assertRaisesRegex(GateDenied,'consent_boundary'):q.execute_next(s,calls.append)
  self.assertEqual(calls,[]);self.assertEqual(q.boundary_log[-1]['event'],'execute_blocked')
 def test_review_decision_immutable(self):
  with self.assertRaises(AttributeError):self.d.observed_href='https://bank.example/changed'
 def test_cross_domain_and_nonallowlisted_source_denied(self):
  s=copy.deepcopy(self.s);s['control']['href']='https://attacker.example/details'
  with self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
  s=copy.deepcopy(self.s);s['source_url']='https://attacker.example/accounts'
  with self.assertRaises(GateDenied):make_review_decision(s,'B','reviewed')
 def test_control_only_consent_and_zero_width_blocked(self):
  for text in ['I accept terms','You con\u200bsent to sharing']:
   s=copy.deepcopy(self.s);s['control']['text']=text;s['source_html']='<a href="'+self.href+'">'+text+'</a>'
   with self.assertRaisesRegex(GateDenied,'consent_boundary'):make_review_decision(s,'B','reviewed')
 def test_duplicate_exact_anchors_denied(self):
  s=copy.deepcopy(self.s);s['source_html']+=s['source_html']
  with self.assertRaisesRegex(GateDenied,'ambiguous_duplicate_anchor'):make_review_decision(s,'B','reviewed')
 def test_additional_control_attributes_preserved_and_changes_denied(self):
  s=copy.deepcopy(self.s);s['control']['target']='_self';c=copy.deepcopy(self.c);c['control']=s['control'];d=make_review_decision(s,'B','reviewed');q=ReviewedActionQueue();q.enqueue(c,s,d);calls=[];q.execute_next(s,calls.append);self.assertEqual(len(calls),1)
  q=ReviewedActionQueue();q.enqueue(c,s,d);changed=copy.deepcopy(s);changed['control']['target']='_blank';calls=[]
  with self.assertRaises(GateDenied):q.execute_next(changed,calls.append)
  self.assertEqual(calls,[])
if __name__=='__main__':unittest.main(verbosity=2)
