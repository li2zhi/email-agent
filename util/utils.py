email_template = """  
**主题**: {subject}
**发件人**: {author}
-------------
{email_thread}
-------------
"""


def parse_email(email_input: dict) -> tuple[str, str, str, str]:
    """Parse an email input dictionary into its constituent parts."""

    return (
        email_input["author"],
        email_input["to"],
        email_input["subject"],
        email_input["email_thread"],
    )


def format_email_markdown(subject, author, to, email_thread):
    """Format email details into a nicely formatted markdown string."""

    return email_template.format(subject=subject, author=author, email_thread=email_thread)


def format_for_display(tool_call: dict) -> str:
    """Format a tool call into a readable string for the user."""

    display = ""

    if tool_call["name"] == "write_email":
        display += f'# Email Draft\n\n**To**: {tool_call["args"].get("to")}\n**Subject**: {tool_call["args"].get("subject")}\n\n{tool_call["args"].get("content")}'
    elif tool_call["name"] == "schedule_meeting":
        display += f'# Calendar Invite\n\n**Meeting**: {tool_call["args"].get("subject")}\n**Attendees**: {", ".join(tool_call["args"].get("attendees"))}'
    elif tool_call["name"] == "Question":
        display += f'# Question for User\n\n{tool_call["args"].get("content")}'
    else:
        display += f'# Tool Call: {tool_call["name"]}\n\nArguments:\n{tool_call["args"]}'

    return display


def triage_interrupt(interrupt):
    res_map = {
        "1": "notify",
        "2": "ignore",
        "3": "respond"
    }

    print(f"\n{interrupt['action']}\n{interrupt['description']}")
    opt = input("您的意见是：1-需要进行通知 2-忽略该邮件 3-需要回复该邮件：\n")
    result = {"type": res_map[opt]}

    if res_map[opt] != interrupt['classification']:
        reason = input("您的理由是：\n")
        result["reason"] = reason

    return result


def user_ask_interrupt(interrupt):
    feedback = input(f"\n麻烦确认以下信息：\n------------------\n{interrupt['action']}\n------------------\n")
    return feedback


def email_modify_interrupt(interrupt):
    print(f"\n麻烦确认回复邮件内容：1-无需调整 或者输入修改方案")
    feedback = input(f"\n------------------\n{interrupt['action']}\n------------------\n")
    result = {"modify": False, "res": "无需调整，确认发送"}

    if feedback != "1":
        result = {"modify": True, "res": "需要调整，调整建议请见suggestion字段", "suggestion": feedback}

    return result