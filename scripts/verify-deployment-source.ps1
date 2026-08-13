$ErrorActionPreference = 'Stop'
$metadata = Get-Content -Raw DEPLOYMENT.json | ConvertFrom-Json
$result = node scripts/verify-deployed-source.mjs $metadata.address | ConvertFrom-Json
if ($result.localRawByteSha256 -ne $metadata.contract_sha256) { throw "local source hash mismatch" }
if ($result.rpcDecodedSourceSha256 -ne $metadata.contract_sha256) { throw "decoded RPC source hash mismatch" }
if ($result.genlayerJsSourceSha256 -ne $metadata.contract_sha256) { throw "GenLayerJS source hash mismatch" }
Write-Output "deployed source verified: $($result.rpcDecodedSourceSha256)"
