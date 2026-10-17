"""Offline B2B research scaffolding and structural audits. Python 3.10+, stdlib only."""
import argparse
import csv
import itertools
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMAS = {
    'accounts': 'account_id,legal_name,brand,parent_id,country,product_scope,business_model,transaction_unit,fit_status,external_sourcing_status,demand_status,quantity,quantity_unit,quantity_scope,evidence_ids,next_action'.split(','),
    'people': 'person_id,account_id,name,original_title,function,stage,authority_status,work_country,evidence_ids'.split(','),
    'roles': 'role_id,account_id,original_title,procurement_object,actions,stage,authority_status,evidence_ids'.split(','),
    'routes': 'route_id,person_id,account_id,kind,value_raw,value_normalized,ownership,contact_status,checked_at,evidence_ids,use_basis_status'.split(','),
    'evidence': 'evidence_id,entity_id,field,claim,source_url,source_date,checked_at,location,evidence_status,limits'.split(','),
    'platform_tests': 'test_id,query,object_type,exact_label,object_id,query_status,positive_control,control_status,context,checked_at,evidence_ids'.split(','),
    'decisions': 'decision_id,entity_id,decision,reason,depends_on,supersedes,checked_at,reopen_trigger,evidence_ids'.split(','),
}
ENUMS = {
    'fit_status': {'qualified', 'candidate', 'rejected', 'unknown'},
    'external_sourcing_status': {'confirmed', 'signal', 'unknown', 'not_applicable'},
    'demand_status': {'current_need', 'scale_signal', 'historical', 'unknown'},
    'authority_status': {'confirmed', 'signal', 'unknown'},
    'ownership': {'personal', 'shared', 'company', 'unknown'},
    'contact_status': {'public_only', 'dialed', 'replied', 'unverified'},
    'use_basis_status': {'not_recorded', 'documented', 'restricted'},
    'evidence_status': {'verified', 'historical', 'conflicting', 'unverified'},
    'kind': {'email', 'phone', 'url'},
    'query_status': {'exact_found', 'no_exact', 'pending', 'failed'},
    'control_status': {'pass', 'fail', 'not_run'},
    'decision': {'keep', 'hold', 'reject', 'reopen'},
}

def read_matrix(path):
    """Preserve positional duplicate headers, including historical Meta templates."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        matrix = list(csv.reader(stream))
    if not matrix:
        raise ValueError('Empty file: ' + str(path))
    headers, rows = matrix[0], matrix[1:]
    if any(len(row) != len(headers) for row in rows):
        raise ValueError('Inconsistent row width: ' + str(path))
    return headers, rows

def refs(value):
    return [part.strip() for part in value.split(';') if part.strip()]

def normalize(kind, value):
    value = value.strip()
    if kind == 'email':
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Email syntax requires review')
        return value.lower()
    if kind == 'phone':
        if '(0)' in value and (value.startswith('+') or value.startswith('00')):
            raise ValueError('International trunk notation requires source review')
        ext = re.search(r'(?:ext\.?|extension|x|#)\s*(\d+)\s*$', value, re.I)
        suffix = 'x' + ext.group(1) if ext else ''
        number = value[:ext.start()] if ext else value
        if re.search(r'[^\d\s+().-]', number) or number.count('+') > 1 or ('+' in number and not number.startswith('+')):
            raise ValueError('Phone syntax requires review')
        digits = re.sub(r'\D', '', number)
        if number.startswith('00'):
            digits = digits[2:]
        if not 7 <= len(digits) <= 15:
            raise ValueError('Phone length requires review')
        prefix = '+' if number.startswith(('+', '00')) else ''
        return prefix + digits + suffix
    return value

def init_project(out):
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('Refusing to overwrite a nonempty output: ' + str(out))
    out.mkdir(parents=True, exist_ok=True)
    for name, columns in SCHEMAS.items():
        with (out / (name + '.csv')).open('w', encoding='utf-8-sig', newline='') as f:
            csv.writer(f).writerow(columns)
    shutil.copyfile(Path(__file__).resolve().parents[1] / 'assets/project-brief.json', out / 'project-brief.json')
    return {'created': str(out), 'tables': list(SCHEMAS), 'state': 'empty_not_researched'}

def audit(project):
    project = Path(project)
    issues, data, indexes = [], {}, {}
    def report(level, code, table, row, detail):
        issues.append(dict(level=level, code=code, table=table, row=row, detail=detail))
    for name, required in SCHEMAS.items():
        try:
            headers, rows = read_matrix(project / (name + '.csv'))
            if len(set(headers)) != len(headers):
                raise ValueError('Duplicate headers in working contract')
            if set(required) - set(headers):
                raise ValueError('Missing columns: ' + ','.join(sorted(set(required) - set(headers))))
            data[name] = [dict(zip(headers, r)) for r in rows]
        except (OSError, ValueError, UnicodeError, csv.Error) as exc:
            report('error', 'table_invalid', name, 0, str(exc))
            data[name] = []
        indexes[name] = {}
        for rowno, row in enumerate(data[name], 2):
            key = row[required[0]]
            if not key or key in indexes[name]:
                report('error', 'id_missing_or_duplicate', name, rowno, key)
            indexes[name][key] = row
            for col, val in row.items():
                if col in ENUMS and val not in ENUMS[col]:
                    report('error', 'state_invalid', name, rowno, col + '=' + val)
                if col in {'checked_at', 'source_date'} and val:
                    try:
                        date.fromisoformat(val)
                    except ValueError:
                        report('error', 'date_invalid', name, rowno, col)
    all_ids = set()
    for name, index in indexes.items():
        duplicate = all_ids & set(index)
        if duplicate:
            report('error', 'id_cross_table_collision', name, 0, ','.join(sorted(duplicate)))
        all_ids.update(index)
    evidence = indexes['evidence']
    def strong_field(name, rowno, row, field):
        entity = row[SCHEMAS[name][0]]
        matching = [evidence[eid] for eid in refs(row.get('evidence_ids', '')) if eid in evidence
                    and evidence[eid]['entity_id'] == entity and evidence[eid]['field'] == field
                    and evidence[eid]['evidence_status'] == 'verified']
        if not matching:
            report('error', 'strong_claim_without_field_evidence', name, rowno, field)
    for name, rows in data.items():
        for rowno, row in enumerate(rows, 2):
            for field, target in [('account_id', 'accounts'), ('person_id', 'people'), ('parent_id', 'accounts')]:
                if field in row and field != SCHEMAS[name][0] and row[field] and row[field] not in indexes[target]:
                    report('error', 'broken_entity_reference', name, rowno, field + '=' + row[field])
            if name in {'people', 'roles', 'routes'} and not row.get('account_id'):
                report('error', 'account_required', name, rowno, '')
            for eid in refs(row.get('evidence_ids', '')):
                if eid not in evidence:
                    report('error', 'broken_evidence_reference', name, rowno, eid)
            if name == 'evidence':
                if row['entity_id'] not in all_ids:
                    report('error', 'evidence_entity_unknown', name, rowno, row['entity_id'])
                for field in ['field', 'claim', 'source_url', 'location', 'checked_at']:
                    if not row[field]:
                        report('error', 'evidence_field_missing', name, rowno, field)
            for field, val in row.items():
                if (field in {'fit_status', 'external_sourcing_status', 'authority_status', 'demand_status', 'use_basis_status'}
                    and val in {'qualified', 'confirmed', 'current_need', 'documented'}):
                    strong_field(name, rowno, row, field)
            if name == 'accounts':
                if row['parent_id'] == row['account_id']:
                    report('error', 'self_parent', name, rowno, '')
                if row['quantity']:
                    try:
                        q = Decimal(row['quantity'])
                        if not q.is_finite() or q < 0:
                            raise InvalidOperation
                    except InvalidOperation:
                        report('error', 'quantity_invalid', name, rowno, row['quantity'])
                    if not row['quantity_unit'] or not row['quantity_scope']:
                        report('error', 'quantity_unit_scope_missing', name, rowno, '')
                    strong_field(name, rowno, row, 'quantity')
                if row['fit_status'] == 'qualified' and not all(row[x] for x in ['legal_name', 'product_scope', 'business_model', 'transaction_unit']):
                    report('error', 'qualification_context_missing', name, rowno, '')
            if name == 'routes':
                if row['ownership'] == 'personal' and not row['person_id']:
                    report('error', 'personal_route_without_person', name, rowno, '')
                if row['person_id'] in indexes['people'] and indexes['people'][row['person_id']]['account_id'] != row['account_id']:
                    report('error', 'route_account_person_mismatch', name, rowno, '')
                try:
                    canonical = normalize(row['kind'], row['value_raw'])
                    if not canonical or row['value_normalized'] != canonical:
                        report('error', 'normalization_mismatch', name, rowno, 'Review raw and normalized value')
                    if row['kind'] == 'phone' and canonical and not canonical.startswith('+'):
                        report('warning', 'country_code_unknown', name, rowno, 'National format retained; no country code inferred')
                except ValueError as exc:
                    report('error', 'route_syntax_review', name, rowno, str(exc))
                if row['ownership'] in {'personal', 'shared', 'company'}:
                    strong_field(name, rowno, row, 'ownership')
                if row['contact_status'] in {'dialed', 'replied'}:
                    strong_field(name, rowno, row, 'contact_status')
            if name == 'platform_tests':
                if row['query_status'] == 'no_exact' and (row['control_status'] != 'pass' or not row['positive_control'] or not row['query'] or not row['context'] or not row['checked_at']):
                    report('error', 'invalid_negative_query', name, rowno, 'Negative requires query, context, date and successful control')
                if row['query_status'] == 'exact_found' and not all(row[x] for x in ['exact_label', 'object_type', 'query', 'context', 'checked_at', 'evidence_ids']):
                    report('error', 'exact_result_incomplete', name, rowno, '')
                if row['query_status'] in {'pending', 'failed'}:
                    report('warning', 'platform_not_verified', name, rowno, row['query_status'])
            if name == 'decisions':
                if row['entity_id'] not in all_ids:
                    report('error', 'decision_entity_unknown', name, rowno, row['entity_id'])
                for dep in refs(row['depends_on']):
                    if dep not in all_ids:
                        report('error', 'decision_dependency_unknown', name, rowno, dep)
                if row['supersedes'] and row['supersedes'] not in indexes['decisions']:
                    report('error', 'decision_predecessor_unknown', name, rowno, row['supersedes'])
                if not row['reason'] or not row['checked_at']:
                    report('error', 'decision_reason_date_missing', name, rowno, '')
    route_groups = defaultdict(set)
    for row in data['routes']:
        if row['value_normalized']:
            route_groups[(row['kind'], row['value_normalized'])].add(row['person_id'] or 'account:' + row['account_id'])
    for (kind, _value), owners in route_groups.items():
        if len(owners) > 1:
            report('warning', 'shared_route_multiple_owners', 'routes', 0, kind + ': ' + ','.join(sorted(owners)))
    if not data['accounts']:
        report('warning', 'empty_research', 'accounts', 0, 'No companies researched; no completion claim')
    try:
        brief = json.loads((project / 'project-brief.json').read_text(encoding='utf-8'))
        if not brief.get('product_or_service') or not brief.get('qualification_rules'):
            report('warning', 'brief_incomplete', 'project-brief', 0, 'Define product and qualification rules before qualification')
    except (OSError, ValueError) as exc:
        report('error', 'brief_invalid', 'project-brief', 0, str(exc))
    return {'scope': 'offline_structural_only_not_buyer_validation_or_upload_approval',
            'counts': {name: len(rows) for name, rows in data.items()},
            'unique_route_values': len(route_groups),
            'errors': sum(i['level'] == 'error' for i in issues),
            'warnings': sum(i['level'] == 'warning' for i in issues), 'issues': issues}

def expand_logic(config):
    layers = config.get('layers')
    if not isinstance(layers, list) or not layers:
        raise ValueError('layers must be a nonempty list')
    count = 1
    for layer in layers:
        if not isinstance(layer, list) or not layer or any(not isinstance(x, str) or not x.strip() for x in layer):
            raise ValueError('Each OR layer needs nonempty text terms')
        if len(set(layer)) != len(layer):
            raise ValueError('Duplicate terms in layer')
        count *= len(layer)
    if count > 10000:
        raise ValueError('More than 10000 paths; split review scope')
    return {'path_count': count, 'paths': [list(x) for x in itertools.product(*layers)],
            'scope': 'logical_paths_not_platform_delivery_guarantee'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init').add_argument('--out', required=True)
    sub.add_parser('audit').add_argument('--project', required=True)
    sub.add_parser('logic').add_argument('--config', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init_project(args.out)
        elif args.command == 'audit':
            result = audit(args.project)
        else:
            result = expand_logic(json.loads(Path(args.config).read_text(encoding='utf-8')))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('errors') else 0
    except (OSError, ValueError, csv.Error) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 2

if __name__ == '__main__':
    sys.exit(main())
