#!/usr/bin/env python3
"""Local fixture checks only; no model capability evidence."""
import hashlib
import copy
import json
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCALES = ('cn', 'de', 'en', 'es', 'fr', 'ja', 'ko')
MODEL = 'qwen3.8-omni-flash'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2))


def run(arguments, reason=None):
    result = subprocess.run(['python3', '-B', *map(str, arguments)], capture_output=True, text=True)
    message = result.stdout + result.stderr
    if reason is None:
        assert result.returncode == 0, message
    else:
        assert result.returncode != 0 and reason in message, message
    print('PASS' if reason is None else f'REJECTED ({reason})', message.strip())


def main():
    with tempfile.TemporaryDirectory(prefix='generator-fixture-', dir=os.environ.get('QWEN_DOCS_PROBE_TMPDIR')) as temporary:
        root = Path(temporary)
        spec_dir, sibling, output = root/'input', root/'sibling', root/'output'
        contract = root/'contract.md'
        contract.write_text('Fixture only; no actual model capabilities.\n')
        spec = {'contract': {'path': str(contract), 'sha256': hashlib.sha256(contract.read_bytes()).hexdigest(), 'version': 1}, 'endpoints': {}}
        for locale in LOCALES:
            write(spec_dir/'strings'/f'{locale}.json', {'title': f'{locale} fixture', 'description': '- `model` 1\n- `input` 2'})
        for endpoint, route in (('chat', '/v1/chat/completions'), ('responses', '/v1/responses')):
            field = 'messages' if endpoint == 'chat' else 'input'
            value = [{'role': 'user', 'content': 'fixture'}] if endpoint == 'chat' else 'fixture'
            schema = {'type': 'object', 'required': ['model', field], 'properties': {
                'model': {'type': 'string', 'enum': [{'$model_id': True}]},
                field: {'type': 'array', 'minItems': 1, 'items': {'type': 'object', 'required': ['role', 'content'], 'properties': {'role': {'type': 'string', 'enum': ['user']}, 'content': {'type': 'string'}}}} if endpoint == 'chat' else {'type': 'string'},
            }}
            examples = {'basic': {'summary': {'$text': 'title'}, 'value': {'model': {'$model_id': True}, field: value}}}
            operation = {'description': {'$text': 'description'}, 'requestBody': {'content': {'application/json': {'schema': schema, 'examples': examples}}}, 'responses': {'401': {'$sibling': '/responses/401'}}}
            skeleton = {'openapi': '3.0.3', 'info': {'title': {'$text': 'title'}, 'version': 'fixture'}, 'paths': {route: {'post': operation}}}
            write(spec_dir/f'{endpoint}.json', skeleton)
            spec['endpoints'][endpoint] = {'basis': '文档', 'source': 'fixture', 'skeleton': f'{endpoint}.json', 'title': {'$text': 'title'}, 'note': ''}
            for locale in LOCALES:
                write(sibling/locale/'api-manual/language-series/qwen3.8-max'/f'qwen3.8-max-{endpoint}.json', {'responses': {'401': {'description': f'{locale} unauthorized'}}})
        write(spec_dir/'spec.json', spec)
        command = [HERE/'generate_docs.py', '--spec-dir', spec_dir, '--sibling-repo', sibling, '--output', output]
        original = contract.read_text()
        contract.write_text(original+'changed\n')
        run(command, 'SHA256 changed')
        assert not output.exists()
        contract.write_text(original)
        run(command)
        assert len(list(output.rglob('*.json'))) == 14
        assert len(list(output.rglob('*.mdx'))) == 14
        run([*command, '--check'])
        run([HERE/'check_parity.py', output])
        def output_hashes():
            return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}
        before = output_hashes()
        for endpoint, defect, reason in [
            ('chat', 'missing_example', 'missing required fields'),
            ('chat', 'missing_schema_required', 'schema omits endpoint-required'),
            ('chat', 'empty_messages', 'array length'),
            ('chat', 'wrong_role', 'enum'),
            ('responses', 'missing_example', 'missing required fields'),
            ('responses', 'wrong_type', 'expected string'),
        ]:
            file = spec_dir/f'{endpoint}.json'
            original_schema = json.loads(file.read_text())
            broken = copy.deepcopy(original_schema)
            media = broken['paths']['/v1/chat/completions' if endpoint == 'chat' else '/v1/responses']['post']['requestBody']['content']['application/json']
            field = 'messages' if endpoint == 'chat' else 'input'
            if defect == 'missing_example':
                del media['examples']['basic']['value'][field]
            elif defect == 'missing_schema_required':
                media['schema']['required'].remove(field)
            elif defect == 'empty_messages':
                media['examples']['basic']['value']['messages'] = []
            elif defect == 'wrong_role':
                media['examples']['basic']['value']['messages'][0]['role'] = 'invalid'
            else:
                media['examples']['basic']['value']['input'] = 42
            write(file, broken)
            run(command, reason)
            assert output_hashes() == before, 'Failed validation wrote output'
            write(file, original_schema)
        version = spec['contract'].pop('version')
        write(spec_dir/'spec.json', spec)
        run(command, 'contract.version is required')
        assert output_hashes() == before
        spec['contract']['version'] = version
        write(spec_dir/'spec.json', spec)
        target = output/'de/api-manual/language-series'/MODEL/f'{MODEL}-chat.json'
        doc = json.loads(target.read_text())
        doc['paths']['/v1/chat/completions']['post']['description'] = '- `model` 1'
        write(target, doc)
        run([HERE/'check_parity.py', output], 'description')
        run([*command, '--check'], 'Generated pages drifted')
        run(command)
        spec['endpoints']['messages'] = dict(spec['endpoints']['chat'])
        write(spec_dir/'spec.json', spec)
        run(command, 'Messages requires contract v2')
        assert not list(output.rglob('*-messages.*'))
        del spec['endpoints']['messages']
        write(spec_dir/'spec.json', spec)
        stale = output/'en/api-manual/language-series'/MODEL/f'{MODEL}-messages.json'
        write(stale, {})
        run(command, 'outside the current contract')
        stale.unlink()
        write(spec_dir/'strings/ko.json', {'title': 'fixture'})
        run(command, 'identical keys')
        assert not list(output.rglob('*-messages.*'))
        print('Fixture checks complete; temporary fixture removed on exit.')


if __name__ == '__main__':
    main()
