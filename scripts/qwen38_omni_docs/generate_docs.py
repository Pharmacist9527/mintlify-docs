#!/usr/bin/env python3
"""Render one reviewed endpoint skeleton into seven localized OpenAPI pages.

No model prose or capability defaults live here. A versioned W1 contract and a
reviewed input specification are required before any output file is written.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

LOCALES = ('cn', 'de', 'en', 'es', 'fr', 'ja', 'ko')
MODEL = 'qwen3.8-omni-flash'
SIBLING = 'qwen3.8-max'
PATHS = {'chat': '/v1/chat/completions', 'responses': '/v1/responses', 'messages': '/v1/messages'}
REQUIRED_FIELDS = {'chat': {'model', 'messages'}, 'responses': {'model', 'input'},
                   'messages': {'model', 'messages', 'max_tokens'}}


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(doc, ref):
    if ref == '':
        return doc
    if not ref.startswith('/'):
        raise ValueError(f'Invalid JSON pointer: {ref}')
    node = doc
    for part in ref[1:].split('/'):
        key = part.replace('~1', '/').replace('~0', '~')
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node


def render(node, strings, sibling, locale):
    if isinstance(node, dict):
        if len(node) == 1 and '$text' in node:
            result = strings[node['$text']]
            if not isinstance(result, str) or not result.strip():
                raise ValueError(f'Empty localized text: {locale}/{node["$text"]}')
            return result.replace('{{locale}}', locale)
        if len(node) == 1 and '$sibling' in node:
            return copy.deepcopy(pointer(sibling, node['$sibling']))
        if node == {'$model_id': True}:
            return MODEL
        if any(key.startswith('$') and key not in ('$ref', '$schema') for key in node):
            raise ValueError(f'Unknown template operator: {list(node)}')
        return {key: render(value, strings, sibling, locale) for key, value in node.items()}
    if isinstance(node, list):
        return [render(value, strings, sibling, locale) for value in node]
    if isinstance(node, str):
        return node.replace('{{locale}}', locale)
    return node


def resolve(doc, node):
    seen = set()
    while isinstance(node, dict) and '$ref' in node:
        ref = node['$ref']
        if not ref.startswith('#/') or ref in seen:
            raise ValueError(f'Unsupported or cyclic request schema reference: {ref}')
        seen.add(ref)
        node = pointer(doc, ref[1:])
    return node


def walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def validate_example(doc, schema, value, location):
    """Validate the OpenAPI schema constraints used by these request examples.

    This is a local structural check. Gateway validation and upstream acceptance
    remain separate evidence and are never inferred from this function.
    """
    schema = resolve(doc, schema)
    if schema.get('nullable') and value is None:
        return
    for branch in schema.get('allOf', []):
        validate_example(doc, branch, value, location)
    for keyword in ('oneOf', 'anyOf'):
        if keyword not in schema:
            continue
        matches = 0
        for branch in schema[keyword]:
            try:
                validate_example(doc, branch, value, location)
                matches += 1
            except ValueError:
                pass
        if matches == 0 or (keyword == 'oneOf' and matches != 1):
            raise ValueError(f'{location}: does not match {keyword}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{location}: value outside enum')
    kind = schema.get('type')
    types = {'object': lambda v: isinstance(v, dict), 'array': lambda v: isinstance(v, list),
             'string': lambda v: isinstance(v, str), 'boolean': lambda v: type(v) is bool,
             'integer': lambda v: type(v) is int, 'number': lambda v: type(v) in (int, float),
             'null': lambda v: v is None}
    if kind is not None and (kind not in types or not types[kind](value)):
        raise ValueError(f'{location}: expected {kind}')
    if isinstance(value, dict):
        missing = set(schema.get('required', [])) - value.keys()
        if missing:
            raise ValueError(f'{location}: missing required fields {sorted(missing)}')
        properties = schema.get('properties', {})
        for key, child in value.items():
            if key in properties:
                validate_example(doc, properties[key], child, f'{location}.{key}')
            elif schema.get('additionalProperties') is False:
                raise ValueError(f'{location}: unexpected field {key}')
            elif isinstance(schema.get('additionalProperties'), dict):
                validate_example(doc, schema['additionalProperties'], child, f'{location}.{key}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            raise ValueError(f'{location}: array length outside schema range')
        for index, child in enumerate(value):
            if 'items' in schema:
                validate_example(doc, schema['items'], child, f'{location}[{index}]')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            raise ValueError(f'{location}: string length outside schema range')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            raise ValueError(f'{location}: string does not match pattern')
    if type(value) in (int, float):
        if value < schema.get('minimum', float('-inf')) or value > schema.get('maximum', float('inf')):
            raise ValueError(f'{location}: number outside schema range')


def validate_page(doc, endpoint):
    if set(doc['paths']) != {PATHS[endpoint]}:
        raise ValueError(f'{endpoint}: wrong endpoint path')
    op = doc['paths'][PATHS[endpoint]]['post']
    media = op['requestBody']['content']['application/json']
    request = resolve(doc, media['schema'])
    model = resolve(doc, request['properties']['model'])
    if model.get('enum') != [MODEL] or 'model' not in request.get('required', []):
        raise ValueError(f'{endpoint}: model must be required and fixed to {MODEL}')
    if not REQUIRED_FIELDS[endpoint] <= set(request.get('required', [])):
        raise ValueError(f'{endpoint}: schema omits endpoint-required fields')
    examples = media.get('examples', {})
    if not 1 <= len(examples) <= 2:
        raise ValueError(f'{endpoint}: choose one or two customer request examples')
    for name, example in examples.items():
        body = example.get('value')
        if not isinstance(body, dict) or body.get('model') != MODEL:
            raise ValueError(f'{endpoint}/{name}: wrong model ID')
        validate_example(doc, request, body, f'{endpoint}/{name}')
    for value in walk(doc):
        if isinstance(value, str) and re.search(r'qwen[ -]?3[.-]8[ .-]max|qwen-3-8-max', value, re.I):
            raise ValueError(f'{endpoint}: unreviewed sibling model text remains')
        if isinstance(value, dict) and '$ref' in value and value['$ref'].startswith('#/'):
            pointer(doc, value['$ref'][1:])
    for response in op['responses'].values():
        for media_type in response.get('content', {}).values():
            for name, example in media_type.get('examples', {}).items():
                validate_example(doc, media_type['schema'], example['value'], f'{endpoint}/response/{name}')
    return [dict(endpoint=endpoint, name=k, body=v['value']) for k, v in examples.items()]


def build(spec_dir, sibling_repo):
    spec = load(spec_dir / 'spec.json')
    contract = spec['contract']
    if type(contract.get('version')) is not int or contract['version'] < 1:
        raise ValueError('contract.version is required and must be a positive integer')
    contract_file = Path(contract['path'])
    if not contract_file.is_file() or digest(contract_file) != contract['sha256']:
        raise ValueError('W1 contract is missing or its SHA256 changed; reread it before generating')
    if 'error_source' in spec:
        source = spec['error_source']
        if not Path(source['path']).is_file() or digest(Path(source['path'])) != source['sha256']:
            raise ValueError('Gateway error evidence changed; reread it before generating')
    if not {'chat', 'responses'} <= set(spec['endpoints']) or set(spec['endpoints']) - set(PATHS):
        raise ValueError('Include chat and responses; only the three known endpoints are allowed')
    dictionaries = {loc: load(spec_dir / 'strings' / f'{loc}.json') for loc in LOCALES}
    if any(set(value) != set(dictionaries['en']) for value in dictionaries.values()):
        raise ValueError('All seven string tables must have identical keys')
    files, example_manifest = {}, []
    for endpoint, entry in spec['endpoints'].items():
        if endpoint == 'messages':
            evidence = Path(entry.get('gateway_success_evidence', ''))
            if contract.get('version', 0) < 2 or entry.get('basis') != '实测' or not evidence.is_file():
                raise ValueError('Messages requires contract v2 and gateway success evidence')
            if digest(evidence) != entry.get('gateway_success_sha256'):
                raise ValueError('Messages gateway evidence SHA256 changed or missing')
            observed = load(evidence)
            if observed.get('status') != 200 or observed.get('path') != PATHS[endpoint] or observed.get('response', {}).get('model') != MODEL:
                raise ValueError('Messages evidence must show a successful gateway response with the exact model')
        if entry.get('basis') not in ('实测', '文档') or not entry.get('source'):
            raise ValueError(f'{endpoint}: provide an explicit evidence source')
        skeleton = load(spec_dir / entry['skeleton'])
        for locale in LOCALES:
            sibling_file = sibling_repo / locale / 'api-manual/language-series' / SIBLING / f'{SIBLING}-{endpoint}.json'
            sibling = load(sibling_file)
            doc = render(skeleton, dictionaries[locale], sibling, locale)
            examples = validate_page(doc, endpoint)
            title = render(entry['title'], dictionaries[locale], sibling, locale)
            note = render(entry['note'], dictionaries[locale], sibling, locale)
            if not isinstance(title, str) or not isinstance(note, str) or SIBLING in title + note:
                raise ValueError(f'{endpoint}/{locale}: invalid MDX text')
            stem = Path(locale) / 'api-manual/language-series' / MODEL / f'{MODEL}-{endpoint}'
            files[Path(str(stem) + '.json')] = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
            # JSON quoting is also valid YAML quoting; it prevents title syntax drift.
            files[Path(str(stem) + '.mdx')] = (
                f'---\ntitle: {json.dumps(title, ensure_ascii=False)}\n'
                f"openapi: '/{stem}.json POST {PATHS[endpoint]}'\n---\n\n{note.strip()}\n")
            if locale == 'en':
                example_manifest.extend(examples)
    return files, {'contract': contract, 'examples': example_manifest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec-dir', required=True, type=Path)
    parser.add_argument('--sibling-repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    # Build and validate every page before touching the output directory.
    files, evidence = build(args.spec_dir.resolve(), args.sibling_repo.resolve())
    stale = []
    for locale in LOCALES:
        directory = args.output / locale / 'api-manual/language-series' / MODEL
        if directory.is_dir():
            stale.extend(str(path.relative_to(args.output)) for path in directory.iterdir()
                         if path.suffix in ('.mdx', '.json') and path.relative_to(args.output) not in files)
    if stale:
        raise ValueError('Previously generated pages outside the current contract: ' + ', '.join(stale))
    mismatches = []
    for relative, content in files.items():
        target = args.output / relative
        if args.check:
            if not target.is_file() or target.read_text() != content:
                mismatches.append(str(relative))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    if mismatches:
        raise ValueError('Generated pages drifted: ' + ', '.join(mismatches))
    evidence['outputs'] = {str(key): hashlib.sha256(value.encode()).hexdigest() for key, value in files.items()}
    if not args.check:
        (args.spec_dir / 'generation-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print(f'{"Checked" if args.check else "Generated"} {len(files)} files across {len(LOCALES)} locales')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, OSError, TypeError) as error:
        raise SystemExit(f'Generation refused: {error}')
