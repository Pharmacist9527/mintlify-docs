# Qwen3.8 Omni Flash reference generator

This tool generates the localized OpenAPI JSON and MDX from one reviewed skeleton per endpoint plus seven string tables. It does not publish the site.

Inputs must include a reviewed contract path, SHA-256 and positive integer version. Messages requires version 2 or later, a gateway success record for the exact model, and its SHA-256. Error samples are also bound by SHA-256. Missing or changed evidence fails before page writes.

`prepare_inputs.py` selects the documented subset from same-language Qwen3.8 Max references. Provide the contract, frontend copy JSON and output input directory explicitly. For v2 also provide `--contract-version 2 --messages-evidence <gateway-record> --errors <error-samples>`.

`generate_docs.py --spec-dir <inputs> --sibling-repo <docs-repo> --output <docs-repo>` validates required endpoint fields, example schema constraints and local references before rendering all files. `--check` compares outputs byte for byte. It does not establish real upstream acceptance or verify every JSON Schema keyword.

`check_parity.py <docs-repo> --output <report.json>` discovers all generated endpoints and checks all seven languages, non-prose values and prose structure. `probe_generator.py` runs isolated positive and negative fixtures, including incomplete examples, missing versions, wrong types and stale outputs; it sends no model requests.

Template operators: `$text` reads localized strings, `$sibling` reads a reviewed same-language JSON pointer, `$model_id: true` inserts the exact model, and `{{locale}}` inserts the locale. Do not inherit capability-bearing prose without checking the current contract.

`generation-evidence.json` records request examples and output fingerprints for independent backend validation. Navigation, link checks, strict Mintlify validation, semantic translation review and real gateway validation remain separate checks.
