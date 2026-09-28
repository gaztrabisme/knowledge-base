<#
.SYNOPSIS
    Installs or updates the knowledge-base MCP server.
.DESCRIPTION
    Bootstraps the private repository gaztrabisme/knowledge-base, installs uv if missing,
    downloads and unpacks the code, and runs scripts/install.py.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Edition full
#>

# Usage (default core edition):
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# Usage (full edition):
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Edition full

[CmdletBinding()]
param(
    [ValidateSet('core', 'full')]
    [string]$Edition = 'core',

    [string]$Dir = "$env:USERPROFILE\knowledge-base",

    [switch]$Update,

    [int]$QdrantPort = 6333
)

$ErrorActionPreference = 'Stop'

$proxy = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { $env:HTTP_PROXY }
$proxyArgs = @{}
if (-not [string]::IsNullOrWhiteSpace($proxy)) {
    $webProxy = New-Object -TypeName System.Net.WebProxy -ArgumentList $proxy
    $webProxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
    [System.Net.WebRequest]::DefaultWebProxy = $webProxy
    $proxyArgs = @{
        Proxy = $proxy
        ProxyUseDefaultCredentials = $true
    }
} else {
    if ([System.Net.WebRequest]::DefaultWebProxy) {
        [System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
    }
}

# Ensure TLS 1.2 is enabled for PowerShell 5.1
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {
    # Ignore if already set or unsupported on non-Windows PS Core
}

if ([string]::IsNullOrWhiteSpace($Dir) -or $Dir -eq '\knowledge-base') {
    $Dir = Join-Path $HOME 'knowledge-base'
}

$tokenFromPrompt = $false
$token = $null
$tempZip = $null
$tempExtractDir = $null

try {
    # Resolve token securely
    if ($env:KB_GH_TOKEN -and -not [string]::IsNullOrWhiteSpace($env:KB_GH_TOKEN)) {
        $token = $env:KB_GH_TOKEN
    } else {
        $secureToken = Read-Host -Prompt "Enter GitHub Personal Access Token (fine-grained, Contents: Read-only)" -AsSecureString
        if ($null -eq $secureToken) {
            throw "No token provided."
        }
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
        try {
            $token = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        if ([string]::IsNullOrWhiteSpace($token)) {
            throw "Token cannot be empty."
        }
        $env:KB_GH_TOKEN = $token
        $tokenFromPrompt = $true
    }

    # Install uv if missing
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "uv not found; installing uv..."
        $uvInstallScript = Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" @proxyArgs
        & ([scriptblock]::Create([string]$uvInstallScript))
        $profileDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
        $localBin = Join-Path $profileDir ".local\bin"
        if (Test-Path $localBin) {
            $env:PATH = "$localBin;$env:PATH"
        }
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            $uvExe = Join-Path $localBin "uv.exe"
            if (Test-Path $uvExe) {
                $env:PATH = "$localBin;$env:PATH"
            } else {
                throw "uv was installed but not found on PATH."
            }
        }
    }

    # Create temporary zip path and extraction folder
    $tempGuid = [System.Guid]::NewGuid().ToString('N')
    $tempBase = [System.IO.Path]::GetTempPath()
    $tempZip = Join-Path $tempBase "kb-$tempGuid.zip"
    $tempExtractDir = Join-Path $tempBase "kb-extract-$tempGuid"

    Write-Host "Downloading repository zipball..."
    $zipUrl = "https://api.github.com/repos/gaztrabisme/knowledge-base/zipball/main"
    $headers = @{
        "Authorization"        = "Bearer $token"
        "Accept"               = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
        "User-Agent"           = "knowledge-base-installer"
    }

    try {
        Invoke-WebRequest -Uri $zipUrl -Headers $headers -OutFile $tempZip -UseBasicParsing @proxyArgs
    } catch {
        $status = $null
        if ($_.Exception.Response) {
            try {
                $status = [int]$_.Exception.Response.StatusCode
            } catch {
                # Ignore conversion failure
            }
        }
        if (-not $status -and $_.Exception.StatusCode) {
            try {
                $status = [int]$_.Exception.StatusCode
            } catch {
                # Ignore conversion failure
            }
        }
        if ($status -eq 401 -or $status -eq 403 -or $status -eq 404) {
            throw "GitHub API error (HTTP $status): token expired or lacks Contents: Read on gaztrabisme/knowledge-base."
        }
        throw "Failed to download repository zipball: $_"
    }

    Write-Host "Unpacking archive..."
    Expand-Archive -Path $tempZip -DestinationPath $tempExtractDir -Force

    $subdirs = @(Get-ChildItem -Path $tempExtractDir -Directory)
    if ($subdirs.Count -gt 0) {
        $sourceDir = $subdirs[0].FullName
    } else {
        $sourceDir = $tempExtractDir
    }

    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }

    Write-Host "Copying files to $Dir..."
    if (Get-Command robocopy -ErrorAction SilentlyContinue) {
        # robocopy exit codes 0-7 indicate success
        robocopy "$sourceDir" "$Dir" /E /NP /NFL /NDL | Out-Null
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy failed with exit code $LASTEXITCODE"
        }
        $global:LASTEXITCODE = 0
    } else {
        Get-ChildItem -Path $sourceDir -Force | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $Dir -Recurse -Force
        }
    }

    $installScript = Join-Path $Dir "scripts\install.py"
    if (-not (Test-Path $installScript)) {
        throw "Installer script not found at $installScript"
    }

    Write-Host "Running scripts\install.py with uv..."
    $uvArgs = @(
        "run",
        "--project", $Dir,
        "python", $installScript,
        "--dir", $Dir,
        "--edition", $Edition,
        "--qdrant-port", "$QdrantPort"
    )
    if ($Update) {
        $uvArgs += "--update"
    }

    & uv @uvArgs
    $scriptExit = $LASTEXITCODE
    if ($scriptExit -ne 0) {
        exit $scriptExit
    }
} finally {
    if ($tokenFromPrompt) {
        Remove-Item Env:KB_GH_TOKEN -ErrorAction SilentlyContinue
    }
    $token = $null
    if ($tempZip -and (Test-Path $tempZip)) {
        Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
    }
    if ($tempExtractDir -and (Test-Path $tempExtractDir)) {
        Remove-Item -Path $tempExtractDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
