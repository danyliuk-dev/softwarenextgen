$ErrorActionPreference='Stop'
$r='C:\NextgenQA\variable074'
Start-Transcript -Path "$r\qa.log" -Force
try {
 $installer="$r\NextgenComponents-0.74.0-variable074-win-x64.exe"
 $p=Start-Process $installer -ArgumentList '/S',"/D=$r\app" -Wait -PassThru
 if($p.ExitCode -ne 0){throw "Installer failed $($p.ExitCode)"}
 $node=(Get-ChildItem 'C:\NextgenQA\tools' -Filter node.exe -Recurse | Select-Object -First 1).FullName
 if(!$node){throw 'Node QA tool missing'}
 $env:NEXTGEN_COMPONENTS_USER_DATA="$r\profile"
 $app=Start-Process "$r\app\NextgenComponents.exe" -PassThru
 & $node "$r\components-offline-http.mjs" "$r\profile\engine.log" | Tee-Object "$r\native-check.log"
 if($LASTEXITCODE -ne 0){throw 'Native startup or offline HTTP check failed'}
 'PASS Windows installer, native application startup, batch preview and all offline manual links' | Set-Content "$r\status.txt"
} catch { $_ | Out-String | Set-Content "$r\failure.txt"; 'FAIL' | Set-Content "$r\status.txt"; throw }
finally {
 if($app){taskkill /PID $app.Id /T /F 2>$null | Out-Null}
 Stop-Transcript
}
