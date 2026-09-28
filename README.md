# Mintlify Starter Kit

Use the starter kit to get your docs deployed and ready to customize.

Click the green **Use this template** button at the top of this repo to copy the Mintlify starter kit. The starter kit contains examples with

- Guide pages
- Navigation
- Customizations
- API reference pages
- Use of popular components

**[Follow the full quickstart guide](https://starter.mintlify.com/quickstart)**

## Development

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview your documentation changes locally. To install, use the following command:

```
npm i -g mint
```

Run the following command at the root of your documentation, where your `docs.json` is located:

```
mint dev
```

View your local preview at `http://localhost:3000`.

## Link checks

Run `python3 scripts/check_links.py` before publishing. It checks navigation,
redirect targets, MDX links, OpenAPI file references, and links inside OpenAPI
descriptions. Use root-relative documentation paths such as
`/cn/api-manual/language-series/gpt/responses/responses-reference`: relative
paths such as `./responses-reference` can resolve differently inside parameter
descriptions. Mintlify adds the deployment's `/docs` prefix automatically.

Use `--output /tmp/link-audit.json` for the full results, or
`--include-archived` to also inspect retired documents. Missing OpenAPI schema
references are reported separately as warnings. This offline check does not
validate HTTP responses or rendered anchor IDs; also verify the deployed site
and use `mint broken-links --check-anchors` for MDX checks. Confirm image
warnings against the rendered CDN URL, since the source asset URL can differ.

## Publishing changes

Install our GitHub app from your [dashboard](https://dashboard.mintlify.com/settings/organization/github-app) to propagate changes from your repo to your deployment. Changes are deployed to production automatically after pushing to the default branch.

## Need help?

### Troubleshooting

- If your dev environment isn't running: Run `mint update` to ensure you have the most recent version of the CLI.
- If a page loads as a 404: Make sure you are running in a folder with a valid `docs.json`.

### Resources
- [Mintlify documentation](https://mintlify.com/docs)
- [Mintlify community](https://mintlify.com/community)
