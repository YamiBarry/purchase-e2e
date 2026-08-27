#!/usr/bin/env pwsh
# fast-test.ps1 - Quick compile + run single Spock/Groovy test (bypass Maven lifecycle)
#
# Mirrors fast-test.sh logic:
#   1. groovyc compiles only the single .groovy file
#   2. JUnit Platform Console runs test with 8 parallel threads
#   Compared to mvn test: from 17s+ down to ~3.5s (5x speedup)
#
# Uses "pathing jar" to bypass Windows command line length limit (~8KB)
#
# Built-in dependency: scripts/junit-platform-console-standalone-1.7.2.jar (no download needed)
#
# Prerequisites: run once: mvn install -DskipTests -pl <module> -am -T 8
#
# Usage:
#   .\fast-test.ps1 <ProjectRoot> <ModuleDir> <TestFile>
#
# Example:
#   .\fast-test.ps1 D:\code\sellerportal-service central-sellerportal-service `
#     src/test/groovy/com/yamibuy/central/sellerportal/service/ShipmentServiceTest.groovy

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ProjectRoot,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$ModuleDir,

    [Parameter(Mandatory=$true, Position=2)]
    [string]$TestFile
)

$ErrorActionPreference = "Stop"

# Resolve java executable
$javaExe = "java"
if ($env:JAVA_HOME) {
    $candidate = Join-Path $env:JAVA_HOME "bin\java.exe"
    if (Test-Path $candidate) { $javaExe = $candidate }
}

# Infer fully qualified class name
$relativePath = $TestFile -replace '.*src/test/groovy/', '' -replace '^src/test/groovy/', ''
$FullClass = ($relativePath -replace '\.groovy$', '') -replace '[/\\]', '.'

Write-Host "[INFO] Project: $ProjectRoot"
Write-Host "[INFO] Module: $ModuleDir"
Write-Host "[INFO] File: $ModuleDir\$TestFile"
Write-Host "[INFO] Class: $FullClass"
Write-Host "[INFO] Java: $javaExe"

Push-Location $ProjectRoot
try {
    # Check target\classes exists
    $targetClasses = Join-Path $ModuleDir "target\classes"
    $targetTestClasses = Join-Path $ModuleDir "target\test-classes"
    if (-not (Test-Path $targetClasses)) {
        Write-Host ""
        Write-Host "[ERROR] $targetClasses does not exist" -ForegroundColor Red
        Write-Host "  Please run: mvn install -DskipTests -pl $ModuleDir -am -T 8"
        exit 1
    }

    # Generate classpath (cached 60 min)
    $cpKeyBytes = [System.Text.Encoding]::UTF8.GetBytes("${ProjectRoot}\${ModuleDir}")
    $cpHash = [System.Security.Cryptography.MD5]::Create().ComputeHash($cpKeyBytes)
    $cpKey = [System.BitConverter]::ToString($cpHash).Replace("-","").Substring(0,8).ToLower()
    $cpCache = Join-Path $env:TEMP "fast-test-cp-$cpKey.txt"

    $needRefresh = $true
    if (Test-Path $cpCache) {
        $age = (Get-Date) - (Get-Item $cpCache).LastWriteTime
        if ($age.TotalMinutes -lt 60) { $needRefresh = $false }
    }

    if ($needRefresh) {
        Write-Host ""
        Write-Host "[INFO] Generating classpath (cached 60 min)..."
        mvn dependency:build-classpath -pl "$ModuleDir" -q "-Dmdep.outputFile=$cpCache"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to generate classpath" -ForegroundColor Red
            exit 1
        }
    }

    $cpContent = (Get-Content $cpCache -Raw).Trim()
    $classesDir = (Resolve-Path $targetClasses).Path
    $testClassesDir = (Resolve-Path $targetTestClasses).Path
    $fullCp = "${cpContent};${classesDir};${testClassesDir}"

    # Build pathing jar to bypass Windows command line length limit
    # A pathing jar contains only a MANIFEST.MF with Class-Path entries (file:/// URLs)
    $pathingJar = Join-Path $env:TEMP "fast-test-pathing-$cpKey.jar"
    $pathingAge = $null
    if (Test-Path $pathingJar) {
        $pathingAge = (Get-Date) - (Get-Item $pathingJar).LastWriteTime
    }

    # Resolve jar executable (needed for pathing jar creation)
    $jarExe = "jar"
    if ($env:JAVA_HOME) {
        $jarCandidate = Join-Path $env:JAVA_HOME "bin\jar.exe"
        if (Test-Path $jarCandidate) { $jarExe = $jarCandidate }
    }

    # Rebuild pathing jar if classpath was refreshed or jar is older than 60 min
    if ($needRefresh -or (-not $pathingAge) -or ($pathingAge.TotalMinutes -gt 60)) {
        Write-Host "[INFO] Building pathing jar..."
        $cpEntries = $fullCp -split ';' | Where-Object { $_.Trim() -ne '' }
        # Convert to file:/// URLs for MANIFEST Class-Path
        $urls = $cpEntries | ForEach-Object {
            $absPath = if ([System.IO.Path]::IsPathRooted($_)) { $_ } else { (Resolve-Path $_).Path }
            $uri = ([System.Uri]::new($absPath)).AbsoluteUri
            # Directories need trailing /
            if ((Test-Path $absPath -PathType Container) -and (-not $uri.EndsWith('/'))) {
                $uri = "$uri/"
            }
            $uri
        }
        $classPathValue = $urls -join ' '

        # Create manifest
        $manifestDir = Join-Path $env:TEMP "fast-test-manifest-$cpKey"
        $metaInf = Join-Path $manifestDir "META-INF"
        if (-not (Test-Path $metaInf)) { New-Item -ItemType Directory -Path $metaInf -Force | Out-Null }
        $manifestFile = Join-Path $metaInf "MANIFEST.MF"
        # Manifest lines must be max 72 bytes; split Class-Path value
        $header = "Manifest-Version: 1.0"
        $cpLine = "Class-Path: $classPathValue"
        $manifestLines = @($header)
        # Split cpLine into 70-char continuation lines
        $first = $true
        while ($cpLine.Length -gt 0) {
            if ($first) {
                $chunk = [Math]::Min(70, $cpLine.Length)
                $manifestLines += $cpLine.Substring(0, $chunk)
                $cpLine = $cpLine.Substring($chunk)
                $first = $false
            } else {
                $chunk = [Math]::Min(69, $cpLine.Length)
                $manifestLines += " " + $cpLine.Substring(0, $chunk)
                $cpLine = $cpLine.Substring($chunk)
            }
        }
        $manifestLines += ""
        [System.IO.File]::WriteAllText($manifestFile, ($manifestLines -join "`r`n"), (New-Object System.Text.UTF8Encoding $false))

        # Create jar using jar tool
        & $jarExe cfm "$pathingJar" "$manifestFile" -C "$manifestDir" . 2>$null
        if ($LASTEXITCODE -ne 0) {
            # Fallback: create jar with .NET ZipArchive
            Write-Host "[INFO] jar.exe failed, using .NET fallback..."
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            if (Test-Path $pathingJar) { Remove-Item $pathingJar }
            $zip = [System.IO.Compression.ZipFile]::Open($pathingJar, 'Create')
            $entry = $zip.CreateEntry("META-INF/MANIFEST.MF")
            $writer = New-Object System.IO.StreamWriter($entry.Open())
            $writer.Write(($manifestLines -join "`n"))
            $writer.Close()
            $zip.Dispose()
        }
    }

    # Step 1: groovyc compile single test file
    Write-Host ""
    Write-Host "[COMPILE] $TestFile ..."
    $compileStart = Get-Date
    $testFileFullPath = Join-Path $ModuleDir $TestFile
    & $javaExe -cp "$pathingJar" org.codehaus.groovy.tools.FileSystemCompiler `
        -cp "$pathingJar" `
        -d "$testClassesDir" `
        "$testFileFullPath"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Compilation failed" -ForegroundColor Red
        exit 1
    }
    $compileMs = [int]((Get-Date) - $compileStart).TotalMilliseconds
    Write-Host "  Compile time: ${compileMs}ms"

    # Step 2: Locate JUnit Platform Console Standalone
    # Priority: skills dir > temp cache > download
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $standaloneLocal = Join-Path $scriptDir "junit-platform-console-standalone-1.7.2.jar"
    $standaloneTemp = Join-Path $env:TEMP "junit-platform-console-standalone-1.7.2.jar"

    if (Test-Path $standaloneLocal) {
        $standalone = $standaloneLocal
    } elseif (Test-Path $standaloneTemp) {
        $standalone = $standaloneTemp
    } else {
        Write-Host ""
        Write-Host "[INFO] Downloading junit-platform-console-standalone (first time only)..."
        Invoke-WebRequest `
            -Uri "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.7.2/junit-platform-console-standalone-1.7.2.jar" `
            -OutFile $standaloneTemp
        $standalone = $standaloneTemp
    }

    # Step 3: Run test with 8 parallel threads
    Write-Host ""
    Write-Host "[RUN] Running test (8 parallel threads)..."
    $testStart = Get-Date
    # Cannot use -jar (ignores -cp). Use pathing jar + standalone in classpath, call main class directly.
    # Build a run-time pathing jar that includes standalone + project classpath
    $runCp = "$standalone;$fullCp"
    $runPathingJar = Join-Path $env:TEMP "fast-test-run-pathing-$cpKey.jar"

    # Rebuild run pathing jar
    $runCpEntries = $runCp -split ';' | Where-Object { $_.Trim() -ne '' }
    $runUrls = $runCpEntries | ForEach-Object {
        $absPath = if ([System.IO.Path]::IsPathRooted($_)) { $_ } else { (Resolve-Path $_).Path }
        $uri = ([System.Uri]::new($absPath)).AbsoluteUri
        if ((Test-Path $absPath -PathType Container) -and (-not $uri.EndsWith('/'))) {
            $uri = "$uri/"
        }
        $uri
    }
    $runClassPathValue = $runUrls -join ' '

    $runManifestDir = Join-Path $env:TEMP "fast-test-run-manifest-$cpKey"
    $runMetaInf = Join-Path $runManifestDir "META-INF"
    if (-not (Test-Path $runMetaInf)) { New-Item -ItemType Directory -Path $runMetaInf -Force | Out-Null }
    $runManifestFile = Join-Path $runMetaInf "MANIFEST.MF"
    $runCpLine = "Class-Path: $runClassPathValue"
    $runManifestLines = @("Manifest-Version: 1.0")
    $first = $true
    $tempLine = $runCpLine
    while ($tempLine.Length -gt 0) {
        if ($first) {
            $chunk = [Math]::Min(70, $tempLine.Length)
            $runManifestLines += $tempLine.Substring(0, $chunk)
            $tempLine = $tempLine.Substring($chunk)
            $first = $false
        } else {
            $chunk = [Math]::Min(69, $tempLine.Length)
            $runManifestLines += " " + $tempLine.Substring(0, $chunk)
            $tempLine = $tempLine.Substring($chunk)
        }
    }
    $runManifestLines += ""
    [System.IO.File]::WriteAllText($runManifestFile, ($runManifestLines -join "`r`n"), (New-Object System.Text.UTF8Encoding $false))
    & $jarExe cfm "$runPathingJar" "$runManifestFile" -C "$runManifestDir" . 2>$null

    & $javaExe -cp "$runPathingJar" org.junit.platform.console.ConsoleLauncher `
        "--select-class=$FullClass" `
        "--config=junit.jupiter.execution.parallel.enabled=true" `
        "--config=junit.jupiter.execution.parallel.mode.default=concurrent" `
        "--config=junit.jupiter.execution.parallel.config.strategy=fixed" `
        "--config=junit.jupiter.execution.parallel.config.fixed.parallelism=8" `
        "--details=summary"
    $testExitCode = $LASTEXITCODE
    $testMs = [int]((Get-Date) - $testStart).TotalMilliseconds

    Write-Host ""
    $totalSec = [math]::Round(($compileMs + $testMs) / 1000, 1)
    Write-Host "[SUMMARY] Compile ${compileMs}ms + Run ${testMs}ms = Total ${totalSec}s"

    if ($testExitCode -ne 0) {
        exit $testExitCode
    }
} finally {
    Pop-Location
}
