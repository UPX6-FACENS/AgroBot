# Configura a Evolution API para o bot (cria a instancia se faltar e aponta o webhook).
#
# Uso (PowerShell, dentro da pasta whatsapp):
#   powershell -ExecutionPolicy Bypass -File .\configurar.ps1 -NgrokUrl https://SEU-ENDERECO.ngrok-free.dev
#
# Le EVOLUTION_API_URL, EVOLUTION_API_KEY e EVOLUTION_INSTANCE do arquivo .env desta pasta.
# Pode rodar quantas vezes quiser: se a instancia ja existe, so atualiza o webhook.

param(
    [Parameter(Mandatory = $true)][string]$NgrokUrl
)

$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERRO: nao achei o arquivo .env em $PSScriptRoot" -ForegroundColor Red
    exit 1
}
$cfg = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $cfg[$matches[1]] = $matches[2].Trim() }
}
$base = $cfg["EVOLUTION_API_URL"]
$inst = $cfg["EVOLUTION_INSTANCE"]
$headers = @{ "Content-Type" = "application/json"; "apikey" = $cfg["EVOLUTION_API_KEY"] }

# 1. Espera a Evolution responder (o container demora alguns segundos para subir)
Write-Host "Esperando a Evolution API em $base ..."
$pronto = $false
for ($i = 0; $i -lt 40; $i++) {
    try { Invoke-RestMethod -Uri $base -TimeoutSec 3 | Out-Null; $pronto = $true; break } catch { Start-Sleep -Seconds 3 }
}
if (-not $pronto) {
    Write-Host "ERRO: a Evolution nao respondeu. O Docker Desktop esta aberto? Rodou 'docker compose up -d'?" -ForegroundColor Red
    exit 1
}

# 2. Cria a instancia, se ainda nao existir
$instancias = @(Invoke-RestMethod -Uri "$base/instance/fetchInstances" -Headers $headers)
if ($instancias | Where-Object { $_.name -eq $inst }) {
    Write-Host "Instancia '$inst' ja existe."
} else {
    $body = @{ instanceName = $inst; qrcode = $true; integration = "WHATSAPP-BAILEYS" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/instance/create" -Method Post -Headers $headers -Body $body | Out-Null
    Write-Host "Instancia '$inst' criada."
}

# 3. Aponta o webhook para o endereco do ngrok (sempre terminando em /webhook)
$url = $NgrokUrl.Trim().TrimEnd("/")
if (-not $url.EndsWith("/webhook")) { $url = "$url/webhook" }
$body = @{
    webhook = @{
        enabled         = $true
        url             = $url
        webhookByEvents = $false
        events          = @("MESSAGES_UPSERT")
    }
} | ConvertTo-Json -Depth 5
$resp = Invoke-RestMethod -Uri "$base/webhook/set/$inst" -Method Post -Headers $headers -Body $body
Write-Host "Webhook configurado: $($resp.url)" -ForegroundColor Green

# 3b. Ignora mensagens de grupo. Se o numero do bot participa de grupos e fica dias
#     desconectado, a Evolution tenta processar milhares de mensagens acumuladas ao
#     reconectar: a fila atrasa (ou trava) a mensagem do produtor. O bot nao responde
#     grupos mesmo, entao aqui elas sao descartadas logo na entrada.
$body = @{
    rejectCall      = $false
    msgCall         = ""
    groupsIgnore    = $true
    alwaysOnline    = $false
    readMessages    = $false
    readStatus      = $false
    syncFullHistory = $false
} | ConvertTo-Json
Invoke-RestMethod -Uri "$base/settings/set/$inst" -Method Post -Headers $headers -Body $body | Out-Null
Write-Host "Mensagens de grupo: ignoradas." -ForegroundColor Green

# 4. Mostra se o WhatsApp ja esta conectado
$estado = (Invoke-RestMethod -Uri "$base/instance/connectionState/$inst" -Headers $headers).instance.state
if ($estado -eq "open") {
    Write-Host "WhatsApp CONECTADO. Pode mandar mensagem para o bot." -ForegroundColor Green
} else {
    Write-Host "WhatsApp ainda NAO conectado (estado: $estado)." -ForegroundColor Yellow
    Write-Host "Abra $base/manager no navegador, entre com:"
    Write-Host "   URL:   $base"
    Write-Host "   Chave: $($cfg['EVOLUTION_API_KEY'])"
    Write-Host "Clique na instancia '$inst' e escaneie o QR Code com o celular do BOT"
    Write-Host "(WhatsApp > Aparelhos conectados > Conectar um aparelho)."
    Start-Process "$base/manager"
}
