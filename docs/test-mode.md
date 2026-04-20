# Meshy API Test Mode

Meshy provides a public test mode API key for development and integration testing. It is useful when you want to verify request construction, task polling, response parsing, and download logic without spending Meshy credits.

Official Meshy docs say the test mode key:

- Can be used with Meshy API endpoints.
- Does not consume credits.
- Returns sample task results for valid requests.
- Matches the production API response shape.

Official references:

- https://docs.meshy.ai/en/api/quick-start
- https://docs.meshy.ai/en/api/changelog

## CLI Usage

Check auth using test mode:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py --test-mode --check-auth
```

Create a test-mode dry run:

```bash
python plugins/meshy-prompt-studio/mcp/meshy_mcp_server.py \
  --test-mode \
  --create-text-asset examples/prompts/treasure-chest.prompt.txt \
  --name treasure-chest \
  --preset low_poly_asset \
  --dry-run
```

Test mode is for integration checks only. Use your own Meshy API key for real generation and production asset packs.
