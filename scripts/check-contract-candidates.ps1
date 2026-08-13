$ErrorActionPreference = 'Stop'
$tracked = git ls-files '*.py'
$candidates = @($tracked | Where-Object {
  if (-not (Test-Path $_)) { return $false }
  if ($_ -eq 'contracts/scopelock.py') { return $true }
  return (Get-Content -Raw $_) -match 'from genlayer import|gl\.Contract'
})
$expected = @('contracts/scopelock.py')
Write-Output 'GenVM candidate audit'
Write-Output '---------------------'
foreach ($candidate in $candidates) {
  & "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\Scripts\genvm-lint.exe" check $candidate --json
  if ($LASTEXITCODE -ne 0) { throw "candidate validation failed: $candidate" }
  Write-Output "$candidate    PASS"
}
$unexpected = @($candidates | Where-Object { $_ -notin $expected })
Write-Output "candidate_count: $($candidates.Count)"
Write-Output "validated_count: $($candidates.Count)"
Write-Output "unexpected_candidates: $($unexpected.Count)"
if ($candidates.Count -ne 1 -or $unexpected.Count -ne 0) { throw 'unexpected GenVM contract candidate' }
Write-Output 'result: PASS'
