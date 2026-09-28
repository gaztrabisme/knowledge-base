# Knowledge Base MCP Server

## What It Is and Editions

The Developer Knowledge Base is a local Model Context Protocol (MCP) server that provides semantic search over curated technical books to Claude Code during development sessions. It runs an embedded vector search engine (Qdrant) locally on your machine without relying on external cloud search services.

There are two editions available:
- **core**: The technical books collection covering 17 engineering domains across 291 indexed books. It provides 6 MCP tools (`search`, `search_book`, `read_chunk`, `get_chapter`, `list_books`, and `grep_books`). Installed disk size is approximately 3.5 GB.
- **full**: Includes everything in `core` plus the multilingual philosophy collection (the Original Library, Tao Te Ching translations, and Zhuan Falun in English, Vietnamese, and Chinese) with aligned cross-language passage search. It adds 2 MCP tools (`search_philosophy` and `list_philosophy`), giving 8 tools in total. The full edition adds approximately 0.2 GB to disk size.

On a first-time installation, the installer also downloads approximately 2 GB of embedding and reranker model weights and PyTorch dependencies.

## Create the GitHub Access Token Once

The source repository and release data assets are private. You must create a fine-grained personal access token on GitHub to authenticate downloads on any machine where you install the server.

1. In GitHub, go to:
   **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**
2. Configure the following fields:
   - **Token name**: Choose a descriptive name (for example, `kb-laptop-install`).
   - **Resource owner**: Select `gaztrabisme`.
   - **Expiration**: Select `1 year`.
   - **Repository access**: Select **Only select repositories**, then choose `knowledge-base`.
   - **Permissions**: Expand **Repository permissions**, find **Contents**, and select **Contents: Read-only**. (`Metadata: Read-only` is selected automatically by GitHub).
   - Leave all other permissions unset (None).
3. Click **Generate token** at the bottom of the page and copy the generated token string.
4. Save the token securely. When a machine is retired, return to that GitHub settings page and revoke the token.

## Install on Windows

Because `gaztrabisme/knowledge-base` is a private repository, downloading files through a browser using raw GitHub URLs does not work without being signed in to GitHub. On a new or corporate Windows machine where you cannot sign in to GitHub in a browser, use PowerShell to download `install.ps1` directly through GitHub's Contents API with your token.

Open PowerShell and run this exact 3-line snippet:

```powershell
$token = Read-Host "Enter GitHub Token"
$headers = @{ "Authorization" = "Bearer $token"; "Accept" = "application/vnd.github.raw" }
Invoke-WebRequest "https://api.github.com/repos/gaztrabisme/knowledge-base/contents/install.ps1" -Headers $headers -OutFile install.ps1 -UseBasicParsing
```

Next, run the installer:

- For the **core** edition:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1
  ```

- For the **full** edition:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1 -Edition full
  ```

The installer verifies or installs `uv` (a fast Python package manager), downloads the codebase zipball, preserves any existing data or local configuration, runs the internal setup script to unpack vectors and download model weights, and registers the server with Claude Code.

## Install on macOS and Linux

On macOS and Linux, download `install.sh` via the GitHub Contents API using `curl`:

```bash
read -rsp "Enter GitHub Token: " KB_GH_TOKEN && echo && curl -sSL -H "Authorization: Bearer $KB_GH_TOKEN" -H "Accept: application/vnd.github.raw" "https://api.github.com/repos/gaztrabisme/knowledge-base/contents/install.sh" -o install.sh && chmod +x install.sh
```

Next, run the installer:

- For the **core** edition:
  ```bash
  ./install.sh
  ```

- For the **full** edition:
  ```bash
  ./install.sh --edition full
  ```

## Update, Switch Edition, and Uninstall

### Updating
To update an existing installation to the latest code and index data:
- On Windows:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1 -Update
  ```
- On macOS/Linux:
  ```bash
  ./install.sh --update
  ```
The update preserves your existing `data/`, `bin/`, `qdrant-storage/`, `qdrant-snapshots/`, and `.kb-install.json` files.

### Switching Editions
To switch between `core` and `full` editions on an existing installation, run the installer with the desired edition parameter:
- On Windows:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1 -Edition full
  ```
- On macOS/Linux:
  ```bash
  ./install.sh --edition full
  ```

### Uninstalling
To completely remove the knowledge-base MCP server:
1. Remove the server registration from Claude Code:
   ```bash
   claude mcp remove knowledge-base --scope user
   ```
2. Stop the local Qdrant vector database process if it is running:
   - On Windows:
     ```powershell
     Stop-Process -Name qdrant -Force -ErrorAction SilentlyContinue
     ```
   - On macOS/Linux:
     ```bash
     pkill -f qdrant || true
     ```
3. Delete the installation folder:
   - On Windows:
     ```powershell
     Remove-Item -Recurse -Force "$env:USERPROFILE\knowledge-base"
     ```
   - On macOS/Linux:
     ```bash
     rm -rf ~/knowledge-base
     ```

## Troubleshooting

### HTTP 401 Unauthorized or 404 Not Found
- **Symptom**: The download fails with HTTP 401 or HTTP 404.
- **Cause**: GitHub returns HTTP 404 for private repositories if your token is missing, expired, or lacks access. HTTP 401 indicates an invalid token format.
- **Fix**: Verify that your token was generated under **Resource owner: gaztrabisme**, that repository access is set to **Only select repositories → knowledge-base**, and that permissions include **Contents: Read-only**. If the token has expired, generate a new token.

### Port 6333 Already in Use
- **Symptom**: The installer reports that Qdrant cannot bind to port 6333 because another process is using it.
- **Fix**: Specify an alternate port (such as 6343) using `-QdrantPort` on Windows or `--qdrant-port` on macOS/Linux:
  - Windows:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -QdrantPort 6343
    ```
  - macOS/Linux:
    ```bash
    ./install.sh --qdrant-port 6343
    ```

### Corporate Proxy (HTTPS_PROXY)
- **Symptom**: Network connection times out or fails during download behind an enterprise firewall.
- **Fix**: Define the standard `HTTPS_PROXY` environment variable before running the installer so both the bootstrap script and `uv` route network requests through the proxy:
  - Windows:
    ```powershell
    $env:HTTPS_PROXY = "http://proxy.yourcompany.com:8080"
    ```
  - macOS/Linux:
    ```bash
    export HTTPS_PROXY="http://proxy.yourcompany.com:8080"
    ```

### Windows Execution Policy Blocks Scripts
- **Symptom**: PowerShell outputs `File ... cannot be loaded because running scripts is disabled on this system`.
- **Cause**: Default Windows client policies restrict PowerShell script execution.
- **Fix**: Run PowerShell with the `-ExecutionPolicy Bypass` flag:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1
  ```
  This bypasses the policy only for the current command without modifying persistent system policies.
