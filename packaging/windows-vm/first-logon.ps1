$ErrorActionPreference = 'Stop'
$work = 'C:\NextgenQA'
New-Item -ItemType Directory -Force $work | Out-Null
Remove-Item "$work\status.txt","$work\failure.txt" -ErrorAction SilentlyContinue
Start-Transcript -Path "$work\setup.log" -Append
try {
  $media = (Get-Volume | Where-Object FileSystemLabel -eq 'NEXTGEN_QA' | Select-Object -First 1).DriveLetter + ':'
  if (-not (Test-Path "$media\qa-media.marker")) { throw 'Nextgen QA media missing' }
  New-Item -ItemType Directory -Force "$work\tests" | Out-Null
  Copy-Item "$media\tests\*" "$work\tests" -Recurse -Force
  $node = "$work\tools\node-v24.22.2-win-x64\node.exe"
  if (-not (Test-Path $node)) { Expand-Archive "$media\node-v24.22.2-win-x64.zip" "$work\tools" -Force }
  # Fedora's outer guest-tools bootstrapper is unsigned; pin its independently
  # verified official HTTPS download. Windows still validates driver signatures.
  $guestToolsHash = 'D8AE9EA1E943384AC195E012CD36F82C3161620E5FC9529BE4E42E6F420E222D'
  if ((Get-FileHash "$media\virtio-win-guest-tools.exe" -Algorithm SHA256).Hash -ne $guestToolsHash) { throw 'Guest-tools hash validation failed' }
  if (-not (Get-Service QEMU-GA -ErrorAction SilentlyContinue)) {
    $drivers = Start-Process "$media\virtio-win-guest-tools.exe" -ArgumentList '/install','/quiet','/norestart' -Wait -PassThru
    if ($drivers.ExitCode -notin @(0,3010)) { throw "Guest tools failed: $($drivers.ExitCode)" }
  }
  if (-not (Test-Path "$media\installers")) {
    'READY_FOR_INSTALLERS' | Set-Content "$work\status.txt"
    return
  }
  $results = @()
  foreach ($product in @('components','reports')) {
    $name = if ($product -eq 'components') { 'NextgenComponents' } else { 'Nextgen Reports' }
    $installer = Get-ChildItem "$media\installers\$product\*.exe" | Select-Object -First 1
    $installerHash = (Get-FileHash $installer.FullName -Algorithm SHA256).Hash
    $expected = (Get-Content "$media\installers.json" -Raw | ConvertFrom-Json) | Where-Object product -eq $product
    if ($installerHash -ne $expected.sha256) { throw "Installer hash mismatch: $product" }
    $install = Start-Process $installer.FullName -ArgumentList '/S' -Wait -PassThru
    if ($install.ExitCode -ne 0) { throw "Installer failed: $product $($install.ExitCode)" }
    $directory = Join-Path $env:LOCALAPPDATA "Programs\$name"
    $exe = Join-Path $directory "$name.exe"
    if (-not (Test-Path $exe)) { throw "Installed executable missing: $exe" }
    $sdk = Join-Path $directory 'resources\SDK'
    if (-not (Get-ChildItem "$sdk\NuGet\*.nupkg")) { throw "SDK missing: $product" }
    $port = if ($product -eq 'components') {9367} else {9368}
    if ($product -eq 'components') { $env:NEXTGEN_COMPONENTS_USER_DATA = "$work\profile-components" }
    else { $env:NEXTGEN_DESKTOP_USER_DATA = "$work\profile-reports" }
    $app = Start-Process $exe -ArgumentList "--remote-debugging-port=$port" -PassThru
    $ready = $false
    for ($i=0; $i -lt 120; $i++) {
      try {
        $tabs = Invoke-RestMethod "http://127.0.0.1:$port/json/list"
        if ($tabs | Where-Object { $_.type -eq 'page' -and $_.url.StartsWith('http') }) { $ready=$true;break }
      } catch {}
      Start-Sleep 1
    }
    if (-not $ready) { throw "Application did not start: $product" }
    & $node "$work\tests\offline-app-check.mjs" "$port" $product '2026.10.29.1' | Tee-Object "$work\$product-offline.log"
    if ($LASTEXITCODE -ne 0) { throw "Offline manuals failed: $product" }
    if ($product -eq 'reports') {
      $tab = $tabs | Where-Object type -eq 'page' | Select-Object -First 1
      $origin = ([Uri]$tab.url).GetLeftPart([UriPartial]::Authority)
      & $node "$work\tests\report-examples-browser.mjs" "$port" $origin | Tee-Object "$work\reports-topics.log"
      if ($LASTEXITCODE -ne 0) { throw 'Report topics failed' }
    }
    & $node "$work\tests\capture-native.mjs" "$port" "$work\$product.png"
    & $node "$work\tests\close-desktop.mjs" "$port"
    Start-Sleep 2
    if ($product -eq 'reports') {
      $env:NEXTGEN_STATE_DIRECTORY = "$work\engine-state"
      $env:NEXTGEN_REPORT_URL = 'http://127.0.0.1:5355/'
      $server = Join-Path $directory 'resources\server'
      $engine = Start-Process "$server\NextgenReports.Studio.exe" -ArgumentList '--urls','http://127.0.0.1:5355' -WorkingDirectory $server -PassThru
      try {
        for ($i=0; $i -lt 90; $i++) {
          try { Invoke-RestMethod 'http://127.0.0.1:5355/api/session' | Out-Null; break } catch { Start-Sleep 1 }
        }
        & "$media\consumer\SdkConsumer.exe" | Tee-Object "$work\sdk-client.log"
        if ($LASTEXITCODE -ne 0) { throw 'Installed NuGet client could not render PDF on Windows' }
      } finally { Stop-Process -Id $engine.Id -ErrorAction SilentlyContinue }
    }
    $results += @{ product=$product; installed=$true; installerSha256=$installerHash; sdk=$true; offlineManuals=$true; nativeUi=$true; directory=$directory }
  }
  $results | ConvertTo-Json -Depth 5 | Set-Content "$work\results.json"
  'PASS' | Set-Content "$work\status.txt"
} catch {
  $_ | Out-String | Set-Content "$work\failure.txt"
  'FAIL' | Set-Content "$work\status.txt"
} finally {
  # End the one-time QA autologon; leave normal Windows security enabled.
  $key = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
  Remove-ItemProperty $key -Name DefaultPassword -ErrorAction SilentlyContinue
  Set-ItemProperty $key -Name AutoAdminLogon -Value '0'
  Stop-Transcript
}
