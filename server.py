#!/usr/bin/env python3
"""Static site and a small, allow-listed DeepSeek chat proxy."""
import json
import os
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "public"
PORT = int(os.environ.get("PORT", "3210"))
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
RATE = {}
SYSTEM = """你是“异想物理”的中学力学探索导师。用自然、简洁的中文带学生从具体生活情景理解系统、边界、相互作用、状态和变化。强调“研究对象”：每轮都联系当前集合 S={人,箱子,墙} 中实际选中的成员，解释边界内外作用；若集合为空，提示先点选关注对象。不要强行拼接学科，但在问题自然涉及数量、流动、物质或生命时，可借助数学、化学、生物的思维方式。先接住学生的话，再给一条简短解释，最后提出一个能由当前模拟检验的追问。不要堆公式，不要考试腔，不把猜测说成模拟结果。\n只输出 JSON：{\"reply\":\"面向学生的简短回应\",\"action\":null 或 {\"type\":\"walk\"} 或 {\"type\":\"throw\",\"direction\":\"left\"|\"right\"}}。只有当学生明确要求走路/迈步，或明确要求抛出箱子并指定方向时，才给对应动作；含糊方向时先追问并令 action=null。绝不编造其他 action，不要在 reply 中声称尚未发生的运动。把动作交给本地模拟执行。"""

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json(404, {"error": "Not found"})
            return
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self.send_json(415, {"error": "Expected application/json"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 12000:
            self.send_json(413, {"error": "输入太长，请缩短后重试。"})
            return
        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "请求格式无效。"})
            return
        message = body.get("message") if isinstance(body, dict) else None
        if not isinstance(message, str) or not message.strip():
            self.send_json(400, {"error": "请先描述你想做什么。"})
            return
        allowed = {"人", "箱子", "墙"}
        objects = body.get("objects", [])
        if not isinstance(objects, list):
            objects = []
        objects = [x for x in objects if x in allowed][:3]
        if not API_KEY:
            text = message.strip()
            lowered = text.lower()
            action = None
            if any(word in text for word in ("走路", "迈步", "走一走")):
                action = {"type": "walk"}
                reply = "现在是演示模式：你关注的是 S={" + "，".join(objects) + "}。先观察脚在动时，人的水平位置和速度是否变化；无摩擦地面能否给人水平推力？"
            elif "抛" in text and any(word in text for word in ("左", "向左")):
                action = {"type": "throw", "direction": "left"}
                reply = "现在是演示模式：箱子会按你说的方向抛出。比较抛出前后，研究对象 S={" + "，".join(objects) + "} 的速度怎样变化。"
            elif "抛" in text and any(word in text for word in ("右", "向右")):
                action = {"type": "throw", "direction": "right"}
                reply = "现在是演示模式：箱子会按你说的方向抛出。比较抛出前后，研究对象 S={" + "，".join(objects) + "} 的速度怎样变化。"
            else:
                reply = "现在是演示模式，尚未配置 DeepSeek API Key。你可以先用引导表达“走路”“向左抛箱子”试动作，或先选择研究对象，再提出问题。"
            self.send_json(200, {"reply": reply, "action": action, "demo": True})
            return
        now = time.time()
        ip = self.client_address[0]
        start, count = RATE.get(ip, (now, 0))
        if now - start > 60:
            start, count = now, 0
        count += 1
        RATE[ip] = (start, count)
        if count > 20:
            self.send_json(429, {"error": "请求过于频繁，请稍后再试。"})
            return
        history = body.get("history", [])
        if not isinstance(history, list):
            history = []
        messages = [{"role": "system", "content": SYSTEM}]
        messages.append({"role": "user", "content": f"当前研究对象集合 S={{{'，'.join(objects)}}}。若为空，说明先选择关注对象。"})
        for item in history[-8:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
                messages.append({"role": item["role"], "content": item["content"][:700]})
        messages.append({"role": "user", "content": message.strip()[:500]})
        payload = json.dumps({"model": MODEL, "messages": messages, "response_format": {"type": "json_object"}, "max_tokens": 500, "thinking": {"type": "disabled"}, "temperature": 0.6}).encode()
        request = urllib.request.Request("https://api.deepseek.com/chat/completions", data=payload, headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read())
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            reply = parsed.get("reply") if isinstance(parsed.get("reply"), str) else "先说说你想关注什么，再描述一个动作或问题。"
            reply = reply[:1500]
            raw_action = parsed.get("action")
            action = None
            if isinstance(raw_action, dict) and raw_action.get("type") == "walk":
                action = {"type": "walk"}
            elif isinstance(raw_action, dict) and raw_action.get("type") == "throw" and raw_action.get("direction") in ("left", "right"):
                action = {"type": "throw", "direction": raw_action["direction"]}
            self.send_json(200, {"reply": reply, "action": action})
        except urllib.error.HTTPError as exc:
            print("DeepSeek API error", exc.code, exc.read(500).decode("utf-8", "replace"), flush=True)
            self.send_json(502, {"error": "导师暂时无法回答，请稍后再试。"})
        except Exception as exc:
            print("DeepSeek request failed", str(exc), flush=True)
            self.send_json(502, {"error": "连接导师失败，请检查服务器网络后重试。"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

class Server(ThreadingHTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    Server(("127.0.0.1", PORT), Handler).serve_forever()
