<#
.SYNOPSIS
  Build the package and deploy it to Azure App Service (Linux, Python).

.DESCRIPTION
  Requires Azure CLI and a prior `az login`. With -CreateResources it first creates the
  resource group, a Linux App Service plan and the web app (billed resources; asks for
  confirmation). Without it, it only redeploys the package to an existing app.
  Microsoft Entra ID sign-in is configured afterwards in the Azure portal (manual.md 13.4).

.EXAMPLE
  .\azure\deploy.ps1 -ResourceGroup rg-dane-bu -AppName dane-bu-proplusco -CreateResources
  .\azure\deploy.ps1 -ResourceGroup rg-dane-bu -AppName dane-bu-proplusco
#>
param(
    [Parameter(Mandatory = $true)] [string] $ResourceGroup,
    [Parameter(Mandatory = $true)] [string] $AppName,
    [string] $Location = "westeurope",
    [string] $Sku = "B1",
    [string] $PythonVersion = "3.12",
    [switch] $CreateResources
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$package = Join-Path $root "build\dane-bu-azure.zip"

function Invoke-Az {
    & az @args
    if ($LASTEXITCODE -ne 0) { throw "az $($args -join ' ') zlyhal (kód $LASTEXITCODE)." }
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI nie je nainštalované. Pozrite manual.md, kapitola 13.2."
}
$account = az account show --query "{name:name, id:id}" -o tsv 2>$null
if ($LASTEXITCODE -ne 0) { throw "Nie ste prihlásený. Spustite najprv: az login" }
Write-Host "Subskripcia: $account"

Push-Location $root
try {
    python azure\build_package.py
    if ($LASTEXITCODE -ne 0) { throw "Zostavenie balíka zlyhalo." }
} finally { Pop-Location }

if ($CreateResources) {
    Write-Host ""
    Write-Host "Vytvoria sa tieto prostriedky (plan $Sku je platený):"
    Write-Host "  resource group    $ResourceGroup ($Location)"
    Write-Host "  App Service plan  $AppName-plan (Linux, $Sku)"
    Write-Host "  web app           $AppName (Python $PythonVersion) -> https://$AppName.azurewebsites.net"
    $answer = Read-Host "Pokračovať? Napíšte 'ano'"
    if ($answer -ne "ano") { Write-Host "Zrušené, nič sa nevytvorilo."; exit 1 }

    Invoke-Az group create --name $ResourceGroup --location $Location --output none
    Invoke-Az appservice plan create --resource-group $ResourceGroup --name "$AppName-plan" `
        --is-linux --sku $Sku --output none
    Invoke-Az webapp create --resource-group $ResourceGroup --plan "$AppName-plan" `
        --name $AppName --runtime "PYTHON:$PythonVersion" --output none
    Invoke-Az webapp update --resource-group $ResourceGroup --name $AppName --https-only true --output none
    Invoke-Az webapp config set --resource-group $ResourceGroup --name $AppName `
        --startup-file "sh startup.sh" --min-tls-version "1.2" --output none
    # ZIP deploy installs requirements.txt only with build automation enabled.
    Invoke-Az webapp config appsettings set --resource-group $ResourceGroup --name $AppName `
        --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true --output none
}

Invoke-Az webapp deploy --resource-group $ResourceGroup --name $AppName `
    --src-path $package --type zip --output none
Write-Host ""
Write-Host "Nasadené: https://$AppName.azurewebsites.net"
Write-Host "Bez nastaveného prihlásenia Microsoft Entra ID aplikácia dáta nevydá (manual.md 13.4)."
