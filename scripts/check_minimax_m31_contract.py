#!/usr/bin/env python3
"""检查 MiniMax-M3.1-Flash 七语言 Responses 契约与完整历史回传。

运行：uv run --with jsonschema==4.25.1 python scripts/check_minimax_m31_contract.py
此检查离线运行，不读取 API Key，也不调用模型。
"""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ('cn', 'en', 'de', 'fr', 'ja', 'ko', 'es')
SPEC_PATH = 'api-manual/language-series/minimax-m3.1-flash/minimax-m3.1-flash-responses.json'


def payloads(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'example':
                yield child
            elif key == 'examples':
                for example in child.values():
                    if isinstance(example, dict) and 'value' in example:
                        yield example['value']
            else:
                yield from payloads(child)
    elif isinstance(value, list):
        for child in value:
            yield from payloads(child)


def contract(value):
    if isinstance(value, dict):
        return {
            key: child if key == 'example' else contract(child)
            for key, child in value.items()
            if key != 'tags'
            and not (key in ('title', 'summary', 'description') and isinstance(child, str))
        }
    if isinstance(value, list):
        return [contract(child) for child in value]
    return value


class MinimaxResponsesContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = {locale: json.loads((ROOT / locale / SPEC_PATH).read_text()) for locale in LOCALES}

    def request_validator(self, spec):
        media = spec['paths']['/v1/responses']['post']['requestBody']['content']['application/json']
        return Draft202012Validator({'components': spec['components'], **media['schema']})

    def test_response_output_can_be_reused_in_the_next_request(self):
        for locale, spec in self.specs.items():
            examples = spec['paths']['/v1/responses']['post']['responses']['200']['content']['application/json']['examples']
            for name, example in examples.items():
                with self.subTest(locale=locale, example=name):
                    output = copy.deepcopy(example['value']['output'])
                    history = [{'role': 'user', 'content': 'Answer the question or use the available tool.'}, *output]
                    calls = [item for item in output if item.get('type') == 'function_call']
                    if calls:
                        history.extend({'type': 'function_call_output', 'call_id': item['call_id'],
                                        'output': '{"product_id":"demo-item-001","in_stock":true,"quantity":24}'}
                                       for item in calls)
                    else:
                        history.append({'role': 'user', 'content': 'Continue with a short explanation.'})
                    errors = list(self.request_validator(spec).iter_errors({'model': 'MiniMax-M3.1-Flash', 'input': history}))
                    self.assertFalse(errors, errors[0].message if errors else '')

    def test_reasoning_text_is_not_a_user_message_content_type(self):
        request = {'model': 'MiniMax-M3.1-Flash', 'input': [
            {'type': 'message', 'role': 'user', 'content': [{'type': 'reasoning_text', 'text': 'Not a user text block.'}]}
        ]}
        for locale, spec in self.specs.items():
            with self.subTest(locale=locale):
                self.assertFalse(self.request_validator(spec).is_valid(request))

    def test_error_code_accepts_application_error_codes(self):
        response = {'error': {'code': 'invalid_prompt', 'message': 'Invalid request parameters', 'type': '', 'param': ''}}
        for locale, spec in self.specs.items():
            with self.subTest(locale=locale):
                media = spec['paths']['/v1/responses']['post']['responses']['400']['content']['application/json']
                validator = Draft202012Validator({'components': spec['components'], **media['schema']})
                self.assertTrue(validator.is_valid(response))

    def test_examples_use_english_data_in_every_locale(self):
        for locale, spec in self.specs.items():
            for index, example in enumerate(payloads(spec)):
                with self.subTest(locale=locale, example=index):
                    self.assertTrue(json.dumps(example, ensure_ascii=False).isascii())

    def test_contract_and_examples_match_across_locales(self):
        expected = contract(self.specs['cn'])
        expected_examples = list(payloads(self.specs['cn']))
        for locale, spec in self.specs.items():
            with self.subTest(locale=locale):
                self.assertEqual(contract(spec), expected)
                self.assertEqual(list(payloads(spec)), expected_examples)


if __name__ == '__main__':
    unittest.main(verbosity=2)
