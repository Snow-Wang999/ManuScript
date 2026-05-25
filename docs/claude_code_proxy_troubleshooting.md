# Claude Code / OAuth 登录 403：代理排查备忘

## 典型现象

- `OAuth error: Failed to fetch user roles: Request failed with status code 403`
- 浏览器回调到 `http://localhost:<port>/callback?...` 但提示 `ERR_CONNECTION_REFUSED`

> 注：很多 CLI **不读取 Windows「系统代理/Internet 选项」**，而是优先读取进程环境变量 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY`。环境变量配错时，表现往往像“账号 403/权限问题”。

## 根因示例（本次踩坑）

PowerShell 会话里存在错误的代理环境变量，例如：

- `HTTP_PROXY=http://127.0.0.1:9`
- `HTTPS_PROXY=http://127.0.0.1:9`
- `ALL_PROXY=http://127.0.0.1:9`

端口 `9` 未监听时，所有需要联网的步骤会尝试走这个“假代理”，最终导致 OAuth 请求失败（可能被 CLI 包装成 403/roles 错误）。

## 快速检查（推荐每次先做）

查看当前 PowerShell 会话的代理变量：

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -match 'PROXY' } | Sort-Object Name | Format-Table -AutoSize
```

验证是否被强制走了本机端口（常见错误：指向 `127.0.0.1:9` 等不存在端口）：

```powershell
curl.exe -I https://api.anthropic.com/
```

如果输出里出现 “Failed to connect to 127.0.0.1 port ...”，基本就是代理变量问题。

## 一键修复（仅当前终端会话，不改系统）

先清空代理变量（最稳的验证方式）：

```powershell
Remove-Item Env:HTTP_PROXY,Env:HTTPS_PROXY,Env:ALL_PROXY,Env:NO_PROXY,Env:GIT_HTTP_PROXY,Env:GIT_HTTPS_PROXY -ErrorAction SilentlyContinue
```

然后重试：

- `claude` → `/login`

## 需要走代理时（把端口改成你真实端口）

以常见本地 HTTP 代理端口 `7890` 为例：

```powershell
$env:HTTP_PROXY  = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
$env:NO_PROXY    = "localhost,127.0.0.1,::1"
```

`NO_PROXY` 很重要：OAuth 登录经常会回调到 `localhost`，如果 `localhost` 也被代理/拦截，就会出现回调页面打不开或 `ERR_CONNECTION_REFUSED`。

## 常见坑

### 1) PowerShell 里的 `curl` 不是 curl

PowerShell 默认把 `curl` 映射到 `Invoke-WebRequest`，参数不兼容（例如 `-I`）。

用真 curl：

```powershell
curl.exe -I https://platform.claude.com/
```

### 2) 代理变量“全局污染”

如果你每次新开终端都会自动出现错误的 `*_PROXY`，通常来自：

- 系统环境变量（用户/系统级）
- PowerShell Profile（`$PROFILE`）
- Conda/虚拟环境激活脚本（某些环境会自动注入 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`）
- 代理软件“同步环境变量”功能

排查时，先用上面的“一键清空”验证能否恢复；确认根因后，再去对应位置移除或修正端口。

### 3) 仅检查系统代理不够

可以看系统层 WinHTTP 代理（不等于 CLI 会用）：

```powershell
netsh winhttp show proxy
```

但实际更关键还是：**当前进程环境变量是否被设置成错误代理**。

