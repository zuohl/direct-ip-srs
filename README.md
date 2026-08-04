# FCM IP SRS

自动抓取 [cagedbird043/fcm-hosts-next](https://github.com/cagedbird043/fcm-hosts-next) 的 FCM 优选 IP，并生成 sing-box 规则集（rule-set）。

## 产物

| 文件 | 说明 |
|------|------|
| `fcm_dual_ip.srs.json` | sing-box 规则集源码（双栈 IPv4 + IPv6） |
| `fcm_dual_ip.srs` | 编译后的二进制规则集（sing-box 直接加载） |
| `fcm_dual_ip.version` | 元数据（来源、生成时间、IP 数量） |

## 使用

sing-box 配置中引用：

```json
{
  "route": {
    "rules": [
      {
        "rule_set": ["fcm-ip"],
        "outbound": "direct"
      }
    ]
  },
  "rule_set": [
    {
      "tag": "fcm-ip",
      "type": "remote",
      "url": "https://raw.githubusercontent.com/zuohl/fcm-ip-srs/main/fcm_dual_ip.srs",
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

- 生成 `fcm_dual_ip.srs.json`（源码）和 `fcm_dual_ip.srs`（编译二进制）
- 可通过环境变量覆盖源地址：`FCM_SOURCE_URL=... python3 generate.py`
