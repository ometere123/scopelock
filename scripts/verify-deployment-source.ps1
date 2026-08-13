$ErrorActionPreference = 'Stop'
$metadata = Get-Content -Raw DEPLOYMENT.json | ConvertFrom-Json
$hash = (Get-FileHash contracts/scopelock.py -Algorithm SHA256).Hash.ToLower()
if ($hash -ne $metadata.contract_sha256) { throw "source hash mismatch: $hash" }
Write-Output "source hash verified: $hash"
