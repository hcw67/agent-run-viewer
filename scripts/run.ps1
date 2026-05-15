param(
  [Parameter(Mandatory=$true)]
  [string]$InputPath,

  [string]$OutPath = ""
)

$ErrorActionPreference = "Stop"
chcp 65001 | Out-Null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"

$scriptPath = Join-Path $PSScriptRoot "agent_run_summarizer.py"
if ([string]::IsNullOrWhiteSpace($OutPath)) {
  python $scriptPath --input $InputPath
} else {
  python $scriptPath --input $InputPath --out $OutPath
}