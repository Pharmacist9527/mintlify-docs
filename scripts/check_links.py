#!/usr/bin/env python3
"""检查 Mintlify 导航、重定向、MDX 链接和 OpenAPI 描述中的本地链接。

仅做离线检查；HTTP 状态和动态生成的锚点仍需在实际站点验证。
用法：python3 scripts/check_links.py [--include-archived] [--output /tmp/links.json]
"""

import argparse
import json
import posixpath
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(
    r'!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))'
    r'|(?:href|src)\s*=\s*["\']([^"\']+)["\']'
    r'|^\s*\[[^\]]+\]:\s*(\S+)', re.M
)


def markdown_links(text):
    # 示例代码中的 URL 不是可点击的文档链接。
    text = re.sub(r'(```|~~~)[^\n]*\n.*?\1', '', text, flags=re.S)
    text = re.sub(r'`[^`\n]+`', '', text)
    for match in MARKDOWN_LINK.finditer(text):
        yield next(value for value in match.groups() if value is not None)


def json_strings(value, location=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from json_strings(child, location + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from json_strings(child, location + '/' + str(index))
    elif isinstance(value, str):
        yield location, value


def audit(include_archived=False):
    config = json.loads((ROOT / 'docs.json').read_text())
    redirects = {r['source']: r['destination'] for r in config.get('redirects', [])}
    links, issues, refs, warnings = [], [], [], []
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = [p for p in files if p and Path(p).suffix in ('.mdx', '.json')
             and p != 'docs.json' and (include_archived or not p.startswith('_archived/'))]

    def issue(kind, file, location, url):
        issues.append(dict(kind=kind, file=file, location=location, url=url))

    def add(file, location, url, kind='link'):
        links.append(dict(file=file, location=location, url=url, kind=kind))

    for file in files:
        text = (ROOT / file).read_text()
        if file.endswith('.json'):
            try:
                data = json.loads(text)
            except ValueError as error:
                issue('invalid-json', file, '', str(error))
                continue
            for location, value in json_strings(data):
                if location.endswith(('/description', '/summary')):
                    for url in markdown_links(value):
                        add(file, location, url, 'openapi-description')
                elif location.endswith('/$ref'):
                    refs.append((file, location, value))
                elif '/externalDocs/' in location and location.endswith('/url'):
                    add(file, location, value)
                elif location.endswith('/fallback_suggestion') and value.startswith(('https://', 'http://')):
                    add(file, location, value, 'example-link')
        else:
            for url in markdown_links(text):
                add(file, 'mdx', url)
            match = re.search(r'^openapi:\s*[\'"]?([^\s\'"]+)', text, re.M)
            if match:
                add(file, 'frontmatter/openapi', match[1], 'openapi-file')

    navigation = []
    for location, value in json_strings(config):
        if re.search(r'/pages/\d+$', location):
            navigation.append(value)
            add('docs.json', location, '/' + value.lstrip('/'), 'navigation')
        elif location.endswith(('/href', '/favicon')) or re.search(r'/(?:logo/(?:light|dark)|customCSS/\d+)$', location):
            add('docs.json', location, value, 'config')
    for source, target in redirects.items():
        add('docs.json', 'redirects' + source, target, 'redirect')

    def file_for(path):
        for suffix in ('', '.mdx', '.md'):
            candidate = ROOT / (path.lstrip('/') + suffix)
            if candidate.is_file():
                return candidate
        return None

    for link in links:
        url, file = link['url'], link['file']
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc:
            if parsed.hostname != 'evolink.ai' or not parsed.path.startswith('/docs/'):
                continue
            path = parsed.path[len('/docs'):]
        else:
            path = parsed.path
        if not path:  # 锚点由线上 HTML 或 mint broken-links --check-anchors 检查。
            continue
        if not path.startswith('/'):
            if link['kind'] in ('openapi-description', 'link'):
                issue('relative-doc-link', file, link['location'], url)
            path = posixpath.join('/' + posixpath.dirname(file), path)
        path = posixpath.normpath(unquote(path))
        visited = set()
        while path in redirects:
            if path in visited:
                issue('redirect-cycle', file, link['location'], url)
                break
            visited.add(path)
            path = redirects[path]
            if urlsplit(path).scheme:
                break
            path = posixpath.normpath(unquote(urlsplit(path).path))
        else:
            # Mintlify 会将导航的目录路径重定向到该目录下的首个页面。
            is_nav_directory = any(p.startswith(path.lstrip('/') + '/') for p in navigation)
            if not file_for(path) and not is_nav_directory:
                issue('missing-target', file, link['location'], url)

    json_cache = {}
    for file, location, ref in refs:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc:
            continue
        target = ROOT / file if not parsed.path else ROOT / posixpath.normpath(
            posixpath.join(posixpath.dirname(file), unquote(parsed.path)))
        try:
            if target not in json_cache:
                json_cache[target] = json.loads(target.read_text())
            value = json_cache[target]
            pointer = unquote(parsed.fragment)
            if pointer:
                if not pointer.startswith('/'):
                    raise ValueError('不是 JSON Pointer')
                for key in pointer[1:].split('/'):
                    key = key.replace('~1', '/').replace('~0', '~')
                    value = value[int(key)] if isinstance(value, list) else value[key]
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            # schema 引用不完整与页面 HTTP 404 分开报告。
            warnings.append(dict(kind='invalid-openapi-ref', file=file, location=location, url=ref))

    return dict(summary=dict(files=len(files), navigation=len(navigation), redirects=len(redirects),
                             links=len(links), openapi_refs=len(refs), issues=len(issues),
                             issue_types=dict(Counter(i['kind'] for i in issues)), warnings=len(warnings)),
                issues=issues, warnings=warnings, links=links)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-archived', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.include_archived)
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for problem in result['issues'][:30]:
        print('{kind}: {file} {location} -> {url}'.format(**problem))
    raise SystemExit(bool(result['issues']))
