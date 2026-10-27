#!/usr/bin/env python3
"""Build reviewed input skeletons from the localized Max family structure."""
import argparse
import hashlib
import json
from pathlib import Path
from generate_docs import ERROR_EXAMPLES, canonical_error_body

HERE = Path(__file__).resolve().parent
MODEL = 'qwen3.8-omni-flash'
SIBLING = 'qwen3.8-max'
LOCALES = ('cn', 'de', 'en', 'es', 'fr', 'ja', 'ko')
EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def shared(node, pointer=''):
    """Only prose is localized from the matching source-language document."""
    if isinstance(node, dict):
        result = {}
        for key, value in node.items():
            child = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            result[key] = {'$sibling': child} if key in ('description', 'title', 'summary') and isinstance(value, str) else shared(value, child)
        return result
    if isinstance(node, list):
        return [shared(value, pointer+'/'+str(index)) for index, value in enumerate(node)]
    return MODEL if node == SIBLING else node


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--copy-json', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--contract-version', type=int, default=1)
    parser.add_argument('--messages-evidence', type=Path)
    parser.add_argument('--errors', type=Path)
    args = parser.parse_args()
    copies = json.loads(args.copy_json.read_text())
    if args.messages_evidence and (args.contract_version < 2 or not args.messages_evidence.is_file()):
        raise ValueError('Messages preparation requires v2 and an existing gateway success record')
    spec = {'contract': {'path': str(args.contract.resolve()), 'sha256': hashlib.sha256(args.contract.read_bytes()).hexdigest(), 'version': args.contract_version}, 'endpoints': {}}
    if args.contract_version >= 2 and not args.errors:
        raise ValueError('v2 preparation requires the reviewed gateway error samples')
    errors = json.loads(args.errors.read_text()) if args.errors else None
    if args.errors:
        spec['error_source'] = {'path': str(args.errors.resolve()), 'sha256': hashlib.sha256(args.errors.read_bytes()).hexdigest()}
    price_labels = {'en': 'Current rates', 'cn': '当前费率', 'de': 'Aktuelle Tarife', 'fr': 'Tarifs actuels', 'es': 'Tarifas actuales', 'ja': '現在の料金', 'ko': '현재 요금'}
    output_labels = {'en': 'Maximum output tokens, including reasoning.', 'cn': '生成输出的 Token 上限，包含思考 Token。', 'de': 'Maximale Anzahl der Ausgabetokens einschließlich Denktokens.', 'fr': 'Nombre maximal de tokens de sortie, raisonnement compris.', 'es': 'Máximo de tokens de salida, incluido el razonamiento.', 'ja': '推論を含む出力トークン数の上限。', 'ko': '추론을 포함한 최대 출력 토큰 수입니다.'}
    id_labels = {'en': 'Unique response ID.', 'cn': '本次响应的唯一 ID。', 'de': 'Eindeutige ID dieser Antwort.', 'fr': 'Identifiant unique de cette réponse.', 'es': 'Identificador único de esta respuesta.', 'ja': 'この応答の一意の ID。', 'ko': '이 응답의 고유 ID입니다.'}
    reasoning_labels = {'en': 'Reasoning text returned with the response.', 'cn': '响应返回的思考文本。', 'de': 'Mit der Antwort zurückgegebener Denktext.', 'fr': 'Texte de raisonnement renvoyé avec la réponse.', 'es': 'Texto de razonamiento devuelto con la respuesta.', 'ja': '応答で返される推論テキスト。', 'ko': '응답에 반환된 추론 텍스트입니다.'}
    message_labels = {'en': 'Use Messages for basic text conversations. For images, see Chat documentation; for built-in web search, use Responses.', 'cn': '通过 Messages 进行基本文本对话。图片输入请参照 Chat 文档；内置联网搜索请使用 Responses。', 'de': 'Verwenden Sie Messages für einfache Textgespräche. Für Bilder folgen Sie der Chat-Dokumentation; für integrierte Websuche verwenden Sie Responses.', 'fr': 'Utilisez Messages pour les conversations textuelles de base. Pour les images, consultez Chat ; pour la recherche web intégrée, utilisez Responses.', 'es': 'Use Messages para conversaciones de texto básicas. Para imágenes, consulte Chat; para búsqueda web integrada, use Responses.', 'ja': 'Messages は基本的なテキスト会話に使用します。画像は Chat のドキュメントを参照し、組み込みウェブ検索は Responses を使用してください。', 'ko': 'Messages는 기본 텍스트 대화에 사용합니다. 이미지는 Chat 문서를 참고하고, 내장 웹 검색은 Responses를 사용하세요.'}
    message_billing = {'en': 'Input and output are charged by actual token usage. Cache billing on Messages has not been verified; do not assume a cache discount from this example.', 'cn': '输入与输出按实际 Token 用量计费。Messages 的缓存计费尚未验证，请勿根据此示例假定缓存折扣。', 'de': 'Ein- und Ausgabe werden nach tatsächlichem Tokenverbrauch berechnet. Cache-Abrechnung bei Messages wurde nicht bestätigt; nehmen Sie für dieses Beispiel keinen Cache-Rabatt an.', 'fr': 'L’entrée et la sortie sont facturées selon les tokens réellement consommés. La facturation du cache sur Messages n’est pas vérifiée ; ne supposez pas de remise de cache avec cet exemple.', 'es': 'La entrada y la salida se cobran según los tokens reales. La facturación de caché en Messages no está verificada; no suponga un descuento de caché a partir de este ejemplo.', 'ja': '入出力は実際のトークン使用量で課金されます。Messages のキャッシュ課金は未検証です。この例からキャッシュ割引を想定しないでください。', 'ko': '입력과 출력은 실제 토큰 사용량에 따라 청구됩니다. Messages의 캐시 과금은 검증되지 않았으므로 이 예제에서 캐시 할인을 가정하지 마세요.'}
    message_list_labels = {'en': 'A nonempty list of user and assistant messages. This reference covers plain text content.', 'cn': '非空的 user/assistant 消息列表；本页仅说明纯文本内容。', 'de': 'Eine nicht leere Liste von user- und assistant-Nachrichten. Diese Referenz behandelt reinen Textinhalt.', 'fr': 'Liste non vide de messages user et assistant. Cette référence couvre uniquement le texte brut.', 'es': 'Lista no vacía de mensajes user y assistant. Esta referencia cubre contenido de texto sin formato.', 'ja': 'user と assistant のメッセージの空でないリスト。本ページではプレーンテキストの内容を説明します。', 'ko': '비어 있지 않은 user 및 assistant 메시지 목록입니다. 이 문서는 일반 텍스트 콘텐츠를 다룹니다.'}
    usage_notes = {
        'en': 'Requests a final usage block. The tested Chat search stream did not include complete usage or an end marker.',
        'cn': '请求在流末尾附加用量块。已测 Chat 搜索流未返回完整用量或结束标记。',
        'de': 'Fordert einen abschließenden Nutzungsblock an. Der getestete Chat-Suchstream enthielt weder vollständige Nutzungsdaten noch eine Endmarkierung.',
        'es': 'Solicita un bloque final de uso. El flujo de búsqueda de Chat probado no incluyó datos de uso completos ni un marcador de finalización.',
        'fr': 'Demande un bloc final d’utilisation. Le flux de recherche Chat testé ne contenait ni données d’utilisation complètes ni marqueur de fin.',
        'ja': 'ストリーム末尾の使用量ブロックを要求します。検証した Chat 検索ストリームでは、完全な使用量と終了マーカーが返りませんでした。',
        'ko': '스트림 끝에 사용량 블록을 요청합니다. 테스트한 Chat 검색 스트림에는 완전한 사용량이나 종료 마커가 없었습니다.',
    }
    for locale in LOCALES:
        c = copies['zh' if locale == 'cn' else locale]
        strings = {'title_chat': 'Qwen3.8 Omni Flash · Chat Completions', 'title_responses': 'Qwen3.8 Omni Flash · Responses', 'title_messages': 'Qwen3.8 Omni Flash · Messages',
                   'intro': c['description']+'\n\n'+c['cacheBody']+('\n\n'+c['faq'][2]['answer'] if args.contract_version >= 2 else ''), 'reasoning': c['faq'][1]['answer'], 'search': c['faq'][2]['answer'],
                   'history': c['contextBody'],
                   'output_budget': output_labels[locale], 'response_id': id_labels[locale], 'reasoning_output': reasoning_labels[locale],
                   'messages_intro': message_labels[locale], 'messages_note': '<Note>\n'+message_billing[locale]+'\n</Note>\n\n'+price_labels[locale]+': `CNY / 1M tokens`: `input 0.76` · `output 2.57`.\n',
                   'messages_list': message_list_labels[locale],
                   'include_usage': usage_notes[locale],
                   'note': '<Note>\n'+c['billingNote']+'\n</Note>\n\n'+price_labels[locale]+': '+
                           '`CNY / 1M tokens`: `input 0.76` · `cache_hit 0.10` · `output 2.57`; `web_search CNY 0.0038 / call`.\n'}
        if not args.messages_evidence:
            for key in ('title_messages', 'messages_intro', 'messages_note', 'messages_list'):
                strings.pop(key)
        write(args.output/'strings'/f'{locale}.json', strings)
    endpoints = [('chat','ChatCompletionRequest','/v1/chat/completions'), ('responses','ResponseRequest','/v1/responses')]
    if args.messages_evidence:
        endpoints.append(('messages', 'CreateMessageRequest', '/v1/messages'))
    for endpoint, request_name, route in endpoints:
        source = json.loads((args.repo/f'en/api-manual/language-series/{SIBLING}/{SIBLING}-{endpoint}.json').read_text())
        skeleton = shared(source)
        skeleton['openapi'] = '3.0.3'
        for server in skeleton.get('servers', []):
            server['description'] = 'EvoLink API'
        skeleton['info'] = {'title': {'$text': 'title_'+endpoint}, 'version': '1.0.0'}
        skeleton.pop('tags', None)
        op = skeleton['paths'][route]['post']
        op['summary'] = {'$text': 'title_'+endpoint}
        op['description'] = {'$text': 'messages_intro' if endpoint == 'messages' else 'intro'}
        op['operationId'] = 'qwen38OmniFlash'+endpoint.title()
        op.pop('parameters', None)  # Session behavior remains unverified.
        schemas = skeleton['components']['schemas']
        request = schemas[request_name]
        keep = {'chat': ['model','messages','max_completion_tokens','stream','stream_options','tools'], 'responses': ['model','input','max_output_tokens','reasoning','stream','tools'], 'messages': ['model','messages','max_tokens']}[endpoint]
        request['properties'] = {key: request['properties'][key] for key in keep}
        request['properties']['model']['enum'] = [MODEL]
        request['properties']['model']['example'] = MODEL
        if endpoint in ('chat', 'messages'):
            request['properties']['messages']['minItems'] = 1
        media = op['requestBody']['content']['application/json']
        media['examples'] = {key: media['examples'][key] for key in (('basic',) if endpoint == 'messages' else ('basic','multimodal'))}
        if endpoint == 'chat':
            request['properties']['stream_options']['properties']['include_usage']['description'] = {'$text': 'include_usage'}
            request['properties']['max_completion_tokens']['description'] = {'$text': 'output_budget'}
            request['properties']['reasoning_effort'] = {'type': 'string', 'enum': EFFORTS, 'default': 'xhigh', 'description': {'$text': 'reasoning'}}
            request['properties']['preserve_thinking'] = {'type': 'boolean', 'default': True, 'description': {'$text': 'history'}}
            request['properties']['enable_search'] = {'type': 'boolean', 'default': False, 'description': {'$text': 'search'}}
            request['properties']['search_options'] = {'type': 'object', 'description': {'$text': 'search'}, 'properties': {'search_strategy': {'type': 'string', 'enum': ['agent']}}}
            if args.contract_version >= 2:
                # v2: do not present the incomplete Chat search path as a supported recipe.
                del request['properties']['enable_search']
                del request['properties']['search_options']
            content = schemas['ContentPart']
            content.pop('description', None)
            content['properties'] = {key: content['properties'][key] for key in ('type','text','image_url')}
            content['properties']['type'] = {'type': 'string', 'enum': ['text','image_url']}
            content['properties']['image_url'].pop('description', None)
            content['properties']['image_url']['properties'].pop('detail', None)
            schemas['SystemMessage']['properties']['content'] = {'type': 'string'}
            schemas['UserMessage']['properties']['content'].pop('description', None)
            assistant = schemas['AssistantRequestMessage']['properties']
            assistant['content'] = {'type': 'string'}
            assistant['reasoning_content'] = {'type': 'string', 'description': {'$text': 'history'}}
            retain = {request_name,'SystemMessage','UserMessage','AssistantRequestMessage','ToolMessage','ContentPart','Tool','ChatCompletionResponse','Choice','AssistantMessage','Usage'}
            for name in list(schemas):
                if name not in retain:
                    del schemas[name]
            schemas['Usage'] = {'type': 'object', 'properties': {key: {'type': 'integer'} for key in ('prompt_tokens','completion_tokens','total_tokens')}}
            schemas['Usage']['properties']['prompt_tokens_details'] = {'type': 'object', 'properties': {'cached_tokens': {'type': 'integer'}}}
            schemas['Usage']['properties']['completion_tokens_details'] = {'type': 'object', 'properties': {'reasoning_tokens': {'type': 'integer'}}}
            schemas['AssistantMessage']['properties']['content'].pop('example', None)
            schemas['AssistantMessage']['properties']['reasoning_content']['description'] = {'$text': 'reasoning_output'}
        elif endpoint == 'responses':
            for branch in request['properties']['input']['oneOf']:
                if branch.get('type') == 'string':
                    branch['minLength'] = 1
                elif branch.get('type') == 'array':
                    branch['minItems'] = 1
            request['properties']['reasoning'] = {'type': 'object', 'description': {'$sibling': '/components/schemas/ResponseRequest/properties/reasoning/description'}, 'properties': {'effort': {'type': 'string', 'enum': EFFORTS}}}
            request['properties']['tools']['description'] = {'$text': 'search'}
            schemas['Tool']['properties']['type']['enum'] = ['web_search','function']
            schemas['Usage'] = {'type': 'object', 'properties': {key: {'type': 'integer'} for key in ('input_tokens','output_tokens','total_tokens')}}
            schemas['Usage']['properties']['input_tokens_details'] = {'type': 'object', 'properties': {'cached_tokens': {'type': 'integer'}}}
            schemas['Usage']['properties']['output_tokens_details'] = {'type': 'object', 'properties': {'reasoning_tokens': {'type': 'integer'}}}
            schemas['ResponseObject']['properties']['id']['description'] = {'$text': 'response_id'}
        else:
            request['properties']['messages']['description'] = {'$text': 'messages_list'}
            request['properties']['max_tokens']['description'] = {'$text': 'output_budget'}
            schemas['InputMessage']['properties']['content'] = {'type': 'string'}
            schemas['OutputContentBlock'] = {'type': 'object', 'properties': {'type': {'type': 'string', 'enum': ['text', 'thinking']}, 'text': {'type': 'string'}, 'thinking': {'type': 'string'}, 'signature': {'type': 'string'}}}
            schemas['AnthropicUsage'] = {'type': 'object', 'properties': {'input_tokens': {'type': 'integer'}, 'output_tokens': {'type': 'integer'}}}
            schemas['MessageResponse']['properties']['stop_reason'] = {'type': 'string', 'example': 'end_turn'}
            retain = {request_name, 'InputMessage', 'OutputContentBlock', 'MessageResponse', 'AnthropicUsage'}
            for name in list(schemas):
                if name not in retain:
                    del schemas[name]
            media['examples']['basic']['value'].pop('system', None)
        limit = {'chat': 'max_completion_tokens', 'responses': 'max_output_tokens', 'messages': 'max_tokens'}[endpoint]
        if args.contract_version >= 2:
            request['properties'][limit].update(minimum=1, maximum=131072)
        schemas['ErrorResponse'] = {'type': 'object'}
        if errors:
            schemas['ErrorResponse'] = {'type': 'object', 'required': ['error'], 'properties': {'error': {'type': 'object', 'required': ['message', 'type'], 'properties': {'message': {'type': 'string'}, 'type': {'type': 'string'}, 'code': {'type': 'string'}, 'param': {'type': 'string', 'nullable': True}}}}}
        for status, response in op['responses'].items():
            if status != '200':
                response['content'] = {'application/json': {'schema': {'$ref': '#/components/schemas/ErrorResponse'}}}
                if errors and status in ('400', '401'):
                    examples = {}
                    for name, key in ERROR_EXAMPLES[status].items():
                        sample = errors[key]
                        assert str(sample['status']) == status
                        body = canonical_error_body(sample)
                        examples[name] = {'value': body}
                    response['content']['application/json']['examples'] = examples
            else:
                response['content']['application/json'].pop('examples', None)
                response['content']['application/json'].pop('example', None)
        # Use an accessible vendor example, not the sibling's example.com placeholder.
        if endpoint != 'messages':
            value = media['examples']['multimodal']['value']
            if endpoint == 'chat':
                value['messages'][0]['content'][1]['image_url']['url'] = 'https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg'
            else:
                value['input'][0]['content'][1]['image_url'] = 'https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg'
        write(args.output/f'{endpoint}.json', skeleton)
        spec['endpoints'][endpoint] = {'basis': '实测' if endpoint == 'messages' else '文档', 'source': f'W1 contract v{args.contract_version}; referenced official model and protocol pages',
                                       'skeleton': f'{endpoint}.json', 'title': {'$text': 'title_'+endpoint}, 'note': {'$text': 'messages_note' if endpoint == 'messages' else 'note'}}
        if endpoint == 'messages':
            spec['endpoints'][endpoint]['gateway_success_evidence'] = str(args.messages_evidence.resolve())
            spec['endpoints'][endpoint]['gateway_success_sha256'] = hashlib.sha256(args.messages_evidence.read_bytes()).hexdigest()
    write(args.output/'spec.json', spec)
    print(f'Prepared v{args.contract_version} {len(endpoints)} endpoint skeletons and seven string tables; no output pages rendered.')


if __name__ == '__main__':
    main()
