# Direct IP SRS

生成 sing-box 的**所有直连 IP** 规则集（rule-set）。结果集 = **手动维护的 IP/CIDR** + **FCM 优选 IP**，用于直连（direct）流量分流。

## 手动维护 IP

在 [`direct_ip_manual.json`](direct_ip_manual.json) 中维护需要直连的 IP 或 CIDR 段（`ip_cidr` 数组），可随时增删：

```json
{
  "ip_cidr": [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "fc00::/7",
    "fe80::/10"
  ]
}
```

## 产物

| 文件 | 说明 |
|------|------|
| `direct_ip_manual.json` | 手动维护的直连 IP/CIDR（可编辑） |
| `direct_ip.json` | sing-box 规则集源码（双栈 IPv4 + IPv6） |
| `direct_ip.srs` | 编译后的二进制规则集（sing-box 直接加载） |
| `direct_ip.version` | 元数据（来源、生成时间、手动/FCM/总数） |

## 使用

sing-box 配置中引用：

```json
{
  "route": {
    "rules": [
      {
        "rule_set": ["direct-ip"],
        "outbound": "direct"
      }
    ]
  },
  "rule_set": [
    {
      "tag": "direct-ip",
      "type": "remote",
      "url": "https://raw.githubusercontent.com/zuohl/direct-ip-srs/main/direct_ip.srs",
      "format": "binary",
      "download_detour": "proxy"
    }
  ]
}
```

## 更新频率

GitHub Actions 每天自动运行 4 次（UTC 0/6/12/18 点，即北京时间 8/14/20/2 点）。也可在 Actions 页面手动触发 `workflow_dispatch`。

## 本地运行

需要 Python 3 和 sing-box：

```bash
python3 generate.py
```

- 生成 `direct_ip.json`（源码）和 `direct_ip.srs`（编译二进制）
- 手动 IP 从 `direct_ip_manual.json` 读取
- 可通过环境变量覆盖 FCM 源地址：`FCM_SOURCE_URL=... python3 generate.py`
