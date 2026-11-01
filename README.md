# 异想物理 · 第一关：光滑仓库

从生活里的“如果”进入物理世界。玩家先选择研究对象，再用自然语言描述想做的动作，并观察本地力学模拟的结果。

## 本地运行

```sh
npm start
```

打开 http://localhost:3210 。核心物理模型可用 `npm test` 验证。

## AI 对话配置

复制 `.env.example` 到本机 `.env`，填写 `DEEPSEEK_API_KEY`，然后由 systemd 环境文件提供给服务。真实密钥只存放在本地或服务器环境配置中，不要提交到 GitHub。服务端通过 DeepSeek Chat Completions API 请求 `deepseek-flash`，浏览器端不会接触 API Key。模型只能返回受限的走路或抛箱子动作；实际运动由本地物理模型计算。

## 第一关

人物、箱子和墙会轮流闪烁虚线框，提示可以选择。点选可将对象加入研究系统；再次点选会移出。选好研究对象后，可以输入“走路”“向左抛箱子”等动作，或追问系统边界、相互作用与运动变化。

## 服务器部署

静态文件与对话 API 由 Python 标准库服务提供，Nginx 负责公网 HTTP 并将 `/api/` 转发到本机 `127.0.0.1:3210`。参考 `nginx.conf.example` 和 `mammoth-physics.service.example` 配置 systemd。服务器 API Key 放在 `/etc/mammoth-physics.env`，权限设为仅 root 可读；不放入项目目录、不提交 GitHub。
