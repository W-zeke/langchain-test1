"""
运行入口：暖暖情绪支持助手交互终端
导入智能体大模型层，提供交互式对话界面
"""

import sys

# ============================================================
# 【Windows 编码兼容】
# 打补丁：OpenAI 客户端在序列化请求时会因孤立代理项（lone
# surrogate）失败，在此提前清洗所有消息文本。
# ============================================================
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import langchain_core.messages as _lcm
_orig_msg_init = _lcm.BaseMessage.__init__


def _patched_msg_init(self, content, **kwargs):
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace").decode("utf-8")
    _orig_msg_init(self, content, **kwargs)


_lcm.BaseMessage.__init__ = _patched_msg_init

# 导入智能体
from emotion_agent import get_llm_agent


# ============================================================
# 跨平台输入支持：终端无交互时 fallback 到 GUI 弹窗
# ============================================================
_TK_ROOT = None


def _get_tk_root():
    """惰性获取 tkinter 根窗口（避免重复创建）"""
    global _TK_ROOT
    if _TK_ROOT is None:
        import tkinter as tk
        _TK_ROOT = tk.Tk()
        _TK_ROOT.withdraw()
    return _TK_ROOT


def get_user_input(prompt: str) -> str:
    """
    安全获取用户输入：
    - 终端交互可用 → 标准 input()
    - 否则（如 Code Runner 只读面板）→ tkinter 弹窗
    """
    if sys.stdin.isatty():
        return input(prompt).strip()

    # 非 TTY 环境 → GUI 弹窗
    retries = 0
    while retries < 3:
        try:
            from tkinter import simpledialog
            root = _get_tk_root()
            root.lift()
            root.attributes("-topmost", True)
            result = simpledialog.askstring(
                "暖暖 - 情绪支持助手",
                f"{prompt}\n(输入 quit 或 退出 结束对话)",
                parent=root,
            )
            root.attributes("-topmost", False)
            if result is None:
                from tkinter import messagebox
                quit_ask = messagebox.askyesno(
                    "暖暖", "要退出暖暖情绪助手吗？", parent=root
                )
                if quit_ask:
                    return "quit"
                retries += 1
                continue
            return result.strip()
        except Exception:
            print()
            print("=" * 60)
            print("  检测到当前环境不支持交互输入。")
            print("  请在终端中用以下命令运行：")
            print()
            print("    python run_暖暖.py")
            print()
            print("  或在 VSCode 设置中开启：")
            print('    "code-runner.runInTerminal": true')
            print("=" * 60)
            print()
            sys.exit(1)
    return "quit"


# ============================================================
# 交互主循环
# ============================================================
def main():
    print()
    print("=" * 60)
    print("  [暖暖] -- 你的情绪支持助手")
    print("=" * 60)
    print("  告诉我你的感受，我会用心倾听")
    print("  输入 quit / exit / 退出 结束对话")
    print("=" * 60)
    print()

    while True:
        try:
            raw = get_user_input("你说: ")
            if not raw:
                continue
            if raw.lower() in ("quit", "exit", "退出"):
                print()
                print("暖暖: 很高兴能陪伴你这段时光。无论何时需要，我都在这里。愿你每天都充满阳光！")
                print()
                break

            print("  (暖暖正在思考...)", flush=True)
            reply = get_llm_agent(raw)
            print()
            print(f"暖暖: {reply}")
            print()

        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            print("暖暖: 好的，我们下次再聊。照顾好自己哦！")
            print()
            break
        except UnicodeEncodeError:
            print()
            print("暖暖: 抱歉，我的回复包含了当前终端无法显示的字符。")
            print("      建议用 Windows Terminal 或 VSCode 终端运行~")
            print()
        except Exception as e:
            print(f"出错了: {type(e).__name__}: {e}")
            print("暖暖: 好像出了点小问题，我们重新来一次吧~")
            print()


if __name__ == "__main__":
    main()
