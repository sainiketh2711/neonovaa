import unittest, io, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.engine import split_units, answer_question, make_summary, tokens

class EngineTests(unittest.TestCase):
 def setUp(self):
  self.units=[]
  self.units += split_units('Students can borrow a maximum of three books for 14 days. The late fine is ₹2 per book per day.','guide.txt',page=1)
  self.units += split_units('Faculty members can borrow a maximum of five books for 30 days. Reference books cannot be borrowed.','rules.docx',page=2)
 def test_units_keep_provenance(self): self.assertEqual(self.units[0]['page'],1); self.assertEqual(self.units[0]['source'],'guide.txt')
 def test_student_limit_retrieval(self):
  r=answer_question('How many books can students borrow?',self.units); self.assertEqual(r['status'],'answered'); self.assertTrue(any('three books' in x['text'] for x in r['evidence']))
 def test_faculty_retrieval(self): self.assertIn('five books',answer_question('faculty borrowing limit',self.units)['answer'])
 def test_unknown_rejected(self): self.assertEqual(answer_question('What is the university mascot?',self.units)['status'],'not_found')
 def test_summary(self): self.assertTrue(make_summary(self.units))
 def test_deterministic(self): self.assertEqual(answer_question('late fine per book',self.units),answer_question('late fine per book',self.units))
 def test_alias_rules(self): self.assertIn('loan',tokens('borrow'))

 def test_broad_document_overview(self):
  units=split_units('Machine Learning is a field of artificial intelligence. Supervised learning uses labelled training data. Unsupervised learning finds patterns in data.','ml.txt',page=1)
  r=answer_question('What is this document about?',units)
  self.assertEqual(r['intent'],'overview')
  self.assertIn('Machine Learning',r['answer'])
  self.assertGreaterEqual(len(r['evidence']),2)
 def test_topic_explanation_uses_plain_language_rules(self):
  units=split_units('PCA is a dimensionality reduction technique used to reduce the number of features while preserving important information.','ml.txt',page=1)
  r=answer_question('Explain PCA',units)
  self.assertEqual(r['intent'],'explanation')
  self.assertIn('method',r['answer'])
  self.assertIn('keeping the most useful information',r['answer'])
 def test_follow_up_uses_previous_topic(self):
  units=split_units('PCA is a dimensionality reduction technique. The main limitation of PCA is that components may be difficult to interpret.','ml.txt',page=1)
  r=answer_question('What is its main limitation? ',units,previous_question='Explain PCA')
  self.assertEqual(r['status'],'answered')
  self.assertTrue(any('limitation' in e['text'].lower() for e in r['evidence']))
 def test_focused_limitations_list(self):
  units=split_units('PCA is a dimensionality reduction technique. The main limitation of PCA is that components may be difficult to interpret. PCA transforms correlated variables.','ml.txt',page=1)
  r=answer_question('What are the limitations of PCA?',units)
  self.assertEqual(len(r['evidence']),1)
  self.assertIn('limitation',r['answer'].lower())

if __name__=='__main__': unittest.main(verbosity=2)
