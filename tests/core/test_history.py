import asyncio
from llm_framework.core import HistoryBuffer


def _user(text):
    return {"role": "user", "content": text}


def _assistant(text):
    return {"role": "assistant", "content": text}


def _tool_call(call_id):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": "f", "arguments": "{}"},
            }
        ],
    }


def _tool_result(call_id):
    return {"role": "tool", "tool_call_id": call_id, "content": "ok"}


async def main():
    # basic extend and get
    buf = HistoryBuffer()
    buf.extend([_user("hello"), _assistant("hi")])
    msgs = buf.get()
    assert len(msgs) == 2, f"expected 2, got {len(msgs)}"
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    print("extend + get: OK")

    # system messages are stripped on extend
    buf2 = HistoryBuffer()
    buf2.extend(
        [{"role": "system", "content": "instructions"}, _user("q"), _assistant("a")]
    )
    msgs2 = buf2.get()
    assert all(
        m["role"] != "system" for m in msgs2
    ), "system message leaked into buffer"
    assert len(msgs2) == 2
    print("system message stripped: OK")

    # clear resets the buffer
    buf3 = HistoryBuffer()
    buf3.extend([_user("x"), _assistant("y")])
    buf3._messages.clear()
    assert buf3.get() == []
    print("clear: OK")

    # max_messages eviction — oldest pair removed first
    buf4 = HistoryBuffer(max_messages=2)
    buf4.extend([_user("first"), _assistant("reply1")])
    buf4.extend([_user("second"), _assistant("reply2")])
    msgs4 = buf4.get()
    assert len(msgs4) <= 2, f"eviction failed; got {len(msgs4)} messages"
    contents = [m.get("content") for m in msgs4]
    assert "first" not in contents, "oldest message should have been evicted"
    print("max_messages eviction: OK")

    # max_tokens budget trims excess messages
    buf5 = HistoryBuffer(max_tokens=10)
    long_content = "x" * 400
    buf5.extend([_user(long_content), _assistant(long_content)])
    buf5.extend([_user(long_content), _assistant(long_content)])
    buf5.extend([_user(long_content), _assistant(long_content)])
    token_estimate = buf5._token_estimate()
    assert token_estimate <= int(
        10 * 0.8
    ), f"token estimate {token_estimate} exceeds budget"
    print("max_tokens budget: OK")

    # tool-call action/observation pairs are evicted as a unit
    buf6 = HistoryBuffer(max_messages=2)
    buf6.extend([_tool_call("c1"), _tool_result("c1")])
    buf6.extend([_user("follow-up"), _assistant("answer")])
    msgs6 = buf6.get()
    # the tool call pair should have been evicted; only the Q&A pair remains
    assert all(
        m.get("role") != "tool" for m in msgs6
    ), "tool result should have been evicted"
    print("tool call pair eviction: OK")

    # get() returns a copy, not a reference
    buf7 = HistoryBuffer()
    buf7.extend([_user("a"), _assistant("b")])
    copy = buf7.get()
    copy.append(_user("injected"))
    assert len(buf7.get()) == 2, "get() should return a copy, not the live list"
    print("get() returns copy: OK")

    print("\nAll HistoryBuffer tests passed.")


asyncio.run(main())
