#!/usr/bin/env python3
"""Mutate actual reviewed inputs in an isolated directory; never call a model."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec-dir', type=Path, required=True)
    parser.add_argument('--sibling-repo', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    renderer = Path(__file__).with_name('generate_docs.py')
    cases = ['positive', 'missing_error_source', 'changed_error_example',
             'empty_messages', 'missing_messages', 'missing_min_items',
             'missing_version', 'zero_output_limit', 'missing_messages_limit',
             'bad_success_record', 'bad_success_hash', 'bad_error_hash']
    results = []
    with tempfile.TemporaryDirectory(prefix='reviewed-inputs-', dir=args.scratch) as root:
        root = Path(root)
        for case in cases:
            spec_dir, output = root/case/'input', root/case/'pages'
            shutil.copytree(args.spec_dir, spec_dir)
            spec = load(spec_dir/'spec.json')
            chat = load(spec_dir/'chat.json')
            media = chat['paths']['/v1/chat/completions']['post']['requestBody']['content']['application/json']
            basic = media['examples']['basic']['value']
            if case == 'missing_error_source':
                del spec['error_source']
            elif case == 'changed_error_example':
                examples = chat['paths']['/v1/chat/completions']['post']['responses']['400']['content']['application/json']['examples']
                examples[next(iter(examples))]['value']['error']['message'] = 'This sentence is absent from the gateway evidence.'
            elif case == 'empty_messages':
                basic['messages'] = []
            elif case == 'missing_messages':
                del basic['messages']
            elif case == 'missing_min_items':
                chat['components']['schemas']['ChatCompletionRequest']['properties']['messages'].pop('minItems')
            elif case == 'missing_version':
                del spec['contract']['version']
            elif case == 'zero_output_limit':
                basic['max_completion_tokens'] = 0
            elif case == 'missing_messages_limit':
                messages = load(spec_dir/'messages.json')
                del messages['paths']['/v1/messages']['post']['requestBody']['content']['application/json']['examples']['basic']['value']['max_tokens']
                write(spec_dir/'messages.json', messages)
            elif case == 'bad_success_record':
                entry = spec['endpoints']['messages']
                evidence = load(Path(entry['gateway_success_evidence']))
                evidence['status'] = 400
                file = root/case/'failed-gateway.json'
                write(file, evidence)
                entry['gateway_success_evidence'] = str(file)
                entry['gateway_success_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            elif case == 'bad_success_hash':
                spec['endpoints']['messages']['gateway_success_sha256'] = '0'*64
            elif case == 'bad_error_hash':
                spec['error_source']['sha256'] = '0'*64
            write(spec_dir/'spec.json', spec)
            write(spec_dir/'chat.json', chat)
            command = ['python3', '-B', str(renderer), '--spec-dir', str(spec_dir),
                       '--sibling-repo', str(args.sibling_repo), '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            files = list(output.rglob('*')) if output.exists() else []
            wrote = sum(p.is_file() for p in files)
            expected_success = case == 'positive'
            if expected_success:
                assert result.returncode == 0 and wrote == 42, result.stdout + result.stderr
            else:
                assert result.returncode != 0 and wrote == 0, case + ': bad input reached output'
            results.append({'case': case, 'exit': result.returncode, 'files_written': wrote,
                            'output': (result.stdout + result.stderr).strip()})
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(results)} reviewed-input cases passed; invalid inputs wrote zero pages')


if __name__ == '__main__':
    main()
