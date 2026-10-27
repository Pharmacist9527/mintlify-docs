#!/usr/bin/env python3
"""Compare structure, non-prose values, and semantic tokens across locales."""
import argparse
import collections
import json
import re
from pathlib import Path

LOCALES = ('cn', 'de', 'en', 'es', 'fr', 'ja', 'ko')
MODEL = 'qwen3.8-omni-flash'


def flatten(node, path=()):
    if isinstance(node, dict):
        rows = {path: ('object', tuple(sorted(node)))}
        for key, value in node.items():
            rows.update(flatten(value, (*path, key)))
        return rows
    if isinstance(node, list):
        rows = {path: ('array', len(node))}
        for index, value in enumerate(node):
            rows.update(flatten(value, (*path, str(index))))
        return rows
    return {path: (type(node).__name__, node)}


def norm(value):
    return re.sub(r'/(cn|de|en|es|fr|ja|ko)/', '/LOC/', value)


def points(value):
    codes = re.findall(r'`([^`]+)`', value)
    links = re.findall(r'\[[^]]+\]\(([^)]+)\)', value)
    prose = re.sub(r'`[^`]+`|\[[^]]+\]\([^)]+\)', '', value)
    return (len(re.findall(r'^\s*[-*] ', value, re.M)),
            len([s for s in value.split('\n\n') if s.strip()]),
            sorted(codes), sorted(norm(link) for link in links),
            sorted(re.findall(r'\d+(?:[.,]\d+)*', prose)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('repo', type=Path)
    parser.add_argument('--endpoints', nargs='+')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    def endpoints_for(locale):
        directory = args.repo / locale / 'api-manual/language-series' / MODEL
        return {p.stem[len(MODEL)+1:] for p in directory.glob(f'{MODEL}-*.json')}
    endpoints = set(args.endpoints) if args.endpoints else endpoints_for('en')
    if not {'chat', 'responses'} <= endpoints or endpoints - {'chat', 'responses', 'messages'}:
        raise ValueError('Expected Chat/Responses and optionally Messages')
    if not args.endpoints and any(endpoints_for(locale) != endpoints for locale in LOCALES):
        raise ValueError('The seven locales have different endpoint sets')
    mismatches, counts = [], collections.Counter()
    for endpoint in sorted(endpoints):
        documents = {}
        for locale in LOCALES:
            path = args.repo / locale / 'api-manual/language-series' / MODEL / f'{MODEL}-{endpoint}.json'
            doc = json.loads(path.read_text())
            documents[locale] = flatten(doc)
            for methods in doc['paths'].values():
                examples = methods['post']['requestBody']['content']['application/json'].get('examples', {})
                for key, example in examples.items():
                    body = json.loads(json.dumps(example['value']))
                    if body.get('model') != MODEL:
                        mismatches.append([locale, endpoint, key, 'wrong example model'])
                    counts['parsed_examples'] += 1
            mdx = path.with_suffix('.mdx').read_text()
            expected = f'/{locale}/api-manual/language-series/{MODEL}/{MODEL}-{endpoint}.json POST '
            if expected not in mdx:
                mismatches.append([locale, endpoint, 'mdx', 'wrong OpenAPI target'])
        for locale, translated in documents.items():
            if set(documents['en']) != set(translated):
                mismatches.append([locale, endpoint, 'structure', 'different paths'])
                continue
            for path, (kind, expected) in documents['en'].items():
                other_kind, actual = translated[path]
                if kind != other_kind:
                    mismatches.append([locale, endpoint, path, 'different type'])
                elif kind == 'str':
                    is_prose = path and path[-1] in ('description', 'summary', 'title')
                    left, right = (points(expected), points(actual)) if is_prose else (norm(expected), norm(actual))
                    if left != right:
                        mismatches.append([locale, endpoint, path, left, right])
                elif expected != actual:
                    mismatches.append([locale, endpoint, path, 'structural value changed'])
                counts['compared_fields'] += 1
    report = {'counts': dict(counts), 'mismatches': mismatches,
              'limitation': 'Human translation review and actual backend validation remain necessary.'}
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(bool(mismatches))


if __name__ == '__main__':
    main()
