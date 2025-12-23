# Photo Analysis MCP Server - Setup Guide

This guide explains how to connect the Photo Analysis MCP server to Claude Desktop.

## Quick Setup

Run the automated setup script:

```bash
cd /Users/ycs/photo-app/Travel-website
./setup_claude_mcp.sh
```

Then **restart Claude Desktop** (Cmd+Q to quit, then reopen).

---

## Manual Setup

If you prefer to configure manually:

1. **Edit Claude Desktop config:**
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Add the photo-analysis server:**
   ```json
   {
     "mcpServers": {
       "photo-analysis": {
         "command": "/Users/ycs/.local/bin/uv",
         "args": [
           "run",
           "--directory",
           "/Users/ycs/photo-app/Travel-website",
           "python",
           "mcp/photo_analysis_server.py"
         ]
       }
     }
   }
   ```
   
   **Note:** Use the absolute path to `uv` (run `which uv` to find it) instead of just `uv` to avoid PATH issues.

3. **Restart Claude Desktop**

---

## Available Tools

Once connected, Claude Desktop will have access to these photo analysis tools:

### 1. **analyze_photo**
Run the full analysis pipeline on a travel photo.

**Example prompts:**
- "Analyze this photo at /path/to/image.jpg"
- "Give me a complete analysis of my vacation photo"

**Returns:** Aesthetic scores, categorization, captions, and cost estimate

---

### 2. **assess_aesthetic_quality**
Evaluate aesthetic quality only.

**Example prompts:**
- "What's the aesthetic score of /path/to/photo.jpg?"
- "Rate the composition and lighting of this image"

**Returns:** Scores for composition, framing, lighting, and subject interest (1-5 scale)

---

### 3. **categorize_photo**
Categorize and filter a travel photo.

**Example prompts:**
- "Categorize this travel photo at /path/to/image.jpg"
- "What category does this photo belong to?"

**Returns:** Category, subcategories, time of day, location, and filter status

---

### 4. **generate_caption**
Generate captions at three detail levels.

**Example prompts:**
- "Generate captions for /path/to/photo.jpg"
- "Create a detailed caption for this image"
- "Give me a concise caption for my travel photo"

**Returns:** Concise (<100 chars), standard (150-250 chars), and detailed (300-500 chars) captions plus keywords

---

### 5. **get_token_usage**
View token usage statistics and costs.

**Example prompts:**
- "What's my token usage for photo analysis?"
- "Show me recent analysis costs"

**Returns:** Cost breakdown and usage history

---

## Example Conversation

```
You: What photo analysis tools do you have available?

Claude: I have access to 5 photo analysis tools:
1. analyze_photo - Full pipeline analysis
2. assess_aesthetic_quality - Aesthetic scoring
3. categorize_photo - Categorization and filtering
4. generate_caption - Multi-level caption generation
5. get_token_usage - Cost tracking

You: Analyze the photo at /Users/ycs/photo-app/Travel-website/sample_images/IMG_3339.HEIC

Claude: [Calls analyze_photo tool and returns comprehensive analysis]
```

---

## Troubleshooting

### MCP server not appearing in Claude Desktop

1. **Check the config file is valid JSON:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

2. **Verify uv is installed:**
   ```bash
   which uv
   ```

3. **Test the server manually:**
   ```bash
   cd /Users/ycs/photo-app/Travel-website
   ./scripts/test_mcp.sh
   ```
   The server should start without errors.

4. **Check Claude Desktop logs:**
   - Open Claude Desktop
   - Go to Settings → Advanced → View Logs
   - Look for MCP-related errors

### Tool calls failing

1. **Verify image paths are absolute:**
   ```
   ✅ /Users/ycs/photo-app/Travel-website/sample_images/IMG_3339.HEIC
   ❌ sample_images/IMG_3339.HEIC
   ```

2. **Check Vertex AI credentials:**
   ```bash
   gcloud auth application-default login
   ```

3. **Verify config.yaml is properly configured:**
   - Project ID and location are set
   - All required API keys are present

### High costs

- Use `get_token_usage` tool to monitor spending
- The aesthetic and caption agents use vision models and can be expensive
- Consider setting budget alerts in Google Cloud Console

---

## Configuration

The MCP server uses the same `config.yaml` as the main application. You can adjust:

- **Quality thresholds:** Minimum scores for filtering
- **Model selection:** Which Gemini models to use
- **Token limits:** Maximum tokens per request
- **Logging:** Verbosity and output location

See [config.yaml](file:///Users/ycs/photo-app/Travel-website/config.yaml) for all options.

---

## Security Notes

- The MCP server runs locally on your machine
- It has access to your filesystem (for reading images)
- It uses your Google Cloud credentials for Vertex AI
- All processing happens through your GCP project (costs apply)

**Best practices:**
- Only analyze images you trust
- Monitor your GCP billing
- Keep your config.yaml secure (contains project details)
- Don't share your Claude Desktop config (contains paths)

---

## Uninstalling

To remove the MCP server from Claude Desktop:

1. **Edit the config:**
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Remove the photo-analysis entry:**
   ```json
   {
     "mcpServers": {}
   }
   ```

3. **Restart Claude Desktop**

Your backups are saved as `claude_desktop_config.json.backup.*` files.
