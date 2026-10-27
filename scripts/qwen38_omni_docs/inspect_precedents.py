#!/usr/bin/env python3
"""Measure existing customer docs before choosing the new parameter set."""
import argparse
import collections
import json
import re
from pathlib import Path


def resolve(doc, value):
    while isinstance(value, dict) and value.get('$ref', '').startswith('#/'):
        node = doc
        for part in value['$ref'][2:].split('/'):
            node = node[part.replace('~1', '/').replace('~0', '~')]
        value = node
    return value


def visible(value):
    return re.sub(r'[*`]', '', re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', value))


def inspect(path, root):
    doc = json.loads(path.read_text())
    result = []
    for endpoint, methods in doc.get('paths', {}).items():
        op = methods.get('post')
        if not op:
            continue
        media = op.get('requestBody', {}).get('content', {}).get('application/json', {})
        schema = resolve(doc, media.get('schema', {}))
        props = schema.get('properties', {})
        result.append({
            'file': str(path.relative_to(root)), 'path': endpoint,
            'parameters': list(props), 'parameter_count': len(props),
            'description_lengths': {k: len(visible(resolve(doc, v).get('description', ''))) for k, v in props.items()},
            'intro_lengths': [len(visible(x)) for x in op.get('description', '').splitlines() if x.strip()],
            '400': op.get('responses', {}).get('400', {}).get('description'),
            'example_count': len(media.get('examples', {})),
            'examples': list(media.get('examples', {})),
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('repo', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = args.repo.resolve()
    # Same family plus six recently maintained text API families, from git history.
    peers = {'qwen3.8-max', 'gpt', 'kimi', 'claude', 'deepseek-v4', 'minimax-m3.1-flash', 'glm'}
    entries, all_400, lengths = [], collections.Counter(), []
    for path in sorted((root / 'cn/api-manual/language-series').rglob('*.json')):
        rows = inspect(path, root)
        for row in rows:
            if row['400']:
                all_400[row['400']] += 1
            lengths.extend(row['intro_lengths'])
        if path.relative_to(root / 'cn/api-manual/language-series').parts[0] in peers:
            entries.extend(rows)
    lengths.sort()
    payload = {'source': 'existing cn OpenAPI documents; read-only', 'entries': entries,
               'all_400_distribution': dict(all_400),
               'intro_visible_characters': {'count': len(lengths), 'median': lengths[len(lengths)//2],
                                            'p90': lengths[int((len(lengths)-1)*.9)]}}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print('file | parameters | examples | description characters | intro characters | 400')
    for row in entries:
        print(row['file'], row['parameter_count'], row['example_count'],
              sum(row['description_lengths'].values()), row['intro_lengths'], row['400'], sep=' | ')
    print('intro:', payload['intro_visible_characters'])
    print('400 distribution:', payload['all_400_distribution'])


if __name__ == '__main__':
    main()
