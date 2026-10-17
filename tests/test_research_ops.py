"""Synthetic structural tests; no real customer data, no network."""
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('research_ops', ROOT / 'skills/b2b-buyer-research/scripts/research_ops.py')
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'project'
        ops.init_project(self.path)
        self.rows = {k: [] for k in ops.SCHEMAS}
    def tearDown(self):
        self.tmp.cleanup()
    def add(self, table, **values):
        row = dict.fromkeys(ops.SCHEMAS[table], '')
        defaults = {'fit_status': 'candidate', 'external_sourcing_status': 'unknown', 'demand_status': 'unknown', 'authority_status': 'unknown', 'ownership': 'unknown', 'contact_status': 'unverified', 'use_basis_status': 'not_recorded', 'query_status': 'pending', 'control_status': 'not_run', 'evidence_status': 'unverified'}
        row.update({k: v for k, v in defaults.items() if k in row})
        row.update(values)
        self.rows[table].append(row)
        return row
    def run_audit(self):
        for table, rows in self.rows.items():
            with (self.path / (table + '.csv')).open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=ops.SCHEMAS[table])
                writer.writeheader()
                writer.writerows(rows)
        return ops.audit(self.path)
    def codes(self):
        return {i['code'] for i in self.run_audit()['issues']}
    def test_init_refuses_overwrite(self):
        with self.assertRaises(ValueError): ops.init_project(self.path)
    def test_empty_is_not_completed(self):
        report = self.run_audit()
        self.assertEqual(report['errors'], 0)
        self.assertIn('empty_research', {i['code'] for i in report['issues']})
    def test_shared_phone_does_not_merge_people(self):
        self.add('accounts', account_id='A1')
        for n in (1, 2):
            self.add('people', person_id=f'P{n}', account_id='A1', name=f'Synthetic Person {n}')
            self.add('routes', route_id=f'R{n}', person_id=f'P{n}', account_id='A1', kind='phone', value_raw='+1 202 555 0100', value_normalized='+12025550100')
        report = self.run_audit()
        self.assertEqual(report['errors'], 0)
        self.assertEqual(report['counts']['people'], 2)
        self.assertEqual(report['unique_route_values'], 1)
        self.assertIn('shared_route_multiple_owners', {i['code'] for i in report['issues']})
    def test_strong_claim_needs_same_entity_field(self):
        self.add('accounts', account_id='A1', demand_status='current_need', evidence_ids='E1')
        self.add('accounts', account_id='A2')
        self.add('evidence', evidence_id='E1', entity_id='A2', field='demand_status', claim='Synthetic open procurement', source_url='https://buyer.example/rfq', location='Section 1', checked_at='2026-10-18', evidence_status='verified')
        self.assertIn('strong_claim_without_field_evidence', self.codes())
        self.rows['evidence'][0]['entity_id'] = 'A1'
        self.assertNotIn('strong_claim_without_field_evidence', self.codes())
    def test_quantity_requires_unit_and_source(self):
        self.add('accounts', account_id='A1', quantity='1500')
        self.assertIn('quantity_unit_scope_missing', self.codes())
        self.assertIn('strong_claim_without_field_evidence', self.codes())
    def test_invalid_negative_is_not_absence(self):
        self.add('platform_tests', test_id='T1', query='Synthetic title', query_status='no_exact', control_status='fail', positive_control='Known title', context='Test only', checked_at='2026-10-18')
        self.assertIn('invalid_negative_query', self.codes())
        self.rows['platform_tests'][0]['control_status'] = 'pass'
        self.assertNotIn('invalid_negative_query', self.codes())
    def test_positional_duplicate_meta_headers_preserved(self):
        p = self.path / 'legacy.csv'
        with p.open('w', encoding='utf-8', newline='') as f:
            csv.writer(f).writerows([['email','email','phone'], ['a@buyer.example','b@buyer.example','+12025550100']])
        headers, rows = ops.read_matrix(p)
        self.assertEqual(headers.count('email'), 2)
        self.assertEqual(rows[0][1], 'b@buyer.example')
    def test_duplicate_working_header_rejected(self):
        p = self.path / 'accounts.csv'
        p.write_text('account_id,account_id\nA1,A2\n', encoding='utf-8')
        self.assertGreater(ops.audit(self.path)['errors'], 0)
    def test_normalization_no_country_guess(self):
        self.assertEqual(ops.normalize('phone', '020 7123 4567'), '02071234567')
        self.assertEqual(ops.normalize('phone', '00 44 20 7123 4567 ext 12'), '+442071234567x12')
        self.assertEqual(ops.normalize('email', ' Sales@Buyer.Example '), 'sales@buyer.example')
        with self.assertRaises(ValueError): ops.normalize('phone', '+44 (0)20 7123 4567')
    def test_or_and_all_paths(self):
        result = ops.expand_logic({'layers': [['A','B'], ['X','Y']]})
        self.assertEqual(result['paths'], [['A','X'],['A','Y'],['B','X'],['B','Y']])
        with self.assertRaises(ValueError): ops.expand_logic({'layers': [[]]})
        with self.assertRaises(ValueError): ops.expand_logic({'layers': [['A','A']]})
    def test_wrong_person_company_route(self):
        self.add('accounts', account_id='A1')
        self.add('accounts', account_id='A2')
        self.add('people', person_id='P1', account_id='A1')
        self.add('routes', route_id='R1', person_id='P1', account_id='A2', kind='email', value_raw='a@buyer.example', value_normalized='a@buyer.example')
        self.assertIn('route_account_person_mismatch', self.codes())
    def test_use_basis_does_not_auto_approve(self):
        self.add('accounts', account_id='A1')
        self.add('routes', route_id='R1', account_id='A1', kind='email', value_raw='a@buyer.example', value_normalized='a@buyer.example', use_basis_status='documented')
        self.assertIn('strong_claim_without_field_evidence', self.codes())
        self.assertIn('not_buyer_validation_or_upload_approval', self.run_audit()['scope'])
    def test_five_industries_accept_different_units(self):
        for i, (product, unit) in enumerate([('OEM appliance','units/order'), ('industrial line','project'), ('connector','pieces/year'), ('SaaS','seats/year'), ('consulting','engagement')]):
            self.add('accounts', account_id=f'A{i}', product_scope=product, transaction_unit=unit)
        report = self.run_audit()
        self.assertEqual(report['errors'], 0)
        self.assertEqual(report['counts']['accounts'], 5)

if __name__ == '__main__':
    unittest.main()
