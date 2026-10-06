# Envia o projeto para o GitHub (repositório privado) com travas de segurança.
# Uso (PowerShell, na pasta server-ghost):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\enviar-github.ps1                      # primeira vez
#   .\enviar-github.ps1 "o que mudou"        # próximas atualizações
param([string]$Mensagem = "Atualização do bot Operação Brasil")

$ErrorActionPreference = "Stop"
$Remoto = "https://github.com/KaioADalfior/bot_opbr_dc.git"
Set-Location $PSScriptRoot

function Parar($texto) { Write-Host "`n[PARADO] $texto`n" -ForegroundColor Red; exit 1 }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Parar "Git não instalado. Rode: winget install --id Git.Git  (depois feche e abra o PowerShell)"
}

# 1. Repositório local
if (-not (Test-Path .git)) {
    git init -b main | Out-Null
    Write-Host "Repositório local criado."
}
if (git remote) { git remote set-url origin $Remoto } else { git remote add origin $Remoto }
if (-not (git config user.name))  { git config user.name  (Read-Host "Seu nome (para o histórico do Git)") }
if (-not (git config user.email)) { git config user.email (Read-Host "Seu e-mail do GitHub") }

# 2. Preparar arquivos
git add -A
$arquivos = @(git diff --cached --name-only)

# 3. Travas: nada de segredos, dados ou ambiente virtual
$proibidos = $arquivos | Where-Object {
    $_ -match '(^|/)\.env$' -or $_ -match '^bot/dados/' -or $_ -match '^\.venv' -or
    $_ -match '^estado/.+\.json$' -or $_ -match '^(logs|relatorios)/'
}
if ($proibidos) {
    git reset -q
    Parar ("Estes arquivos NÃO podem ir para o GitHub:`n  " + ($proibidos -join "`n  "))
}
$token = git grep --cached -l -E '[MNO][A-Za-z0-9_-]{23,27}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,40}' -- .
if ($token) {
    git reset -q
    Parar ("Encontrei algo parecido com um TOKEN do Discord em:`n  " + ($token -join "`n  ") +
           "`nRemova o token desse arquivo (ele deve ficar só no bot/.env e no Easypanel).")
}

# 4. Commit
if ($arquivos.Count -gt 0) {
    git commit -q -m $Mensagem
    Write-Host "Commit criado com $($arquivos.Count) arquivo(s)."
} else {
    Write-Host "Nada novo para commitar."
}
git branch -M main

# 5. Trava final: nenhum token em NENHUM commit que vai subir
$historico = @(git rev-list --all)
if ($historico.Count -gt 0) {
    $vaza = git grep -l -E '[MNO][A-Za-z0-9_-]{23,27}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,40}' $historico -- .
    if ($vaza) {
        Parar ("Um commit ANTIGO tem token (nada foi enviado):`n  " + (($vaza | Select-Object -First 5) -join "`n  ") +
               "`nApague o histórico local e rode de novo:`n  Remove-Item -Recurse -Force .git`n  .\enviar-github.ps1")
    }
}

# 6. Push (se o GitHub já tiver um README, junta os históricos antes)
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "O GitHub já tem arquivos; juntando históricos..." -ForegroundColor Yellow
    git pull origin main --allow-unrelated-histories --no-edit
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { Parar "Não foi possível enviar. Copie a mensagem de erro acima e me mande." }
}
Write-Host "`n[OK] Código enviado para $Remoto" -ForegroundColor Green
Write-Host "Agora, no Easypanel, clique em Deploy no App 'bot'.`n"
