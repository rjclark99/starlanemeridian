param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$secretDirectory = Join-Path $ProjectRoot '.secrets'
$keystore = Join-Path $secretDirectory 'release.jks'
$properties = Join-Path $secretDirectory 'android-signing.properties'

if ((Test-Path $keystore) -or (Test-Path $properties)) {
    throw 'Android signing material already exists; refusing to replace the permanent update key.'
}

New-Item -ItemType Directory -Force -Path $secretDirectory | Out-Null
$random = [byte[]]::new(36)
$generator = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $generator.GetBytes($random) } finally { $generator.Dispose() }
$password = [Convert]::ToBase64String($random).TrimEnd('=').Replace('+', '-').Replace('/', '_')
$alias = 'starlane-meridian'
$keytool = Join-Path $env:JAVA_HOME 'bin\keytool.exe'
if (-not (Test-Path $keytool)) { throw 'JAVA_HOME must point to JDK 17 before generating the Android signing key.' }

& $keytool -genkeypair -noprompt -keystore $keystore -storetype PKCS12 -storepass $password -keypass $password -alias $alias -keyalg RSA -keysize 4096 -validity 10000 -dname 'CN=Starlane Meridian, O=Starlane Meridian, C=GB'
if ($LASTEXITCODE -ne 0) { throw 'keytool failed to create the Android signing key.' }

[IO.File]::WriteAllLines($properties, @(
    "storePassword=$password",
    "keyPassword=$password",
    "keyAlias=$alias"
), [Text.UTF8Encoding]::new($false))

Write-Output 'Permanent Android signing key created in the ignored .secrets directory.'
