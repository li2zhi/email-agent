from typing import Literal, TypedDict

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from util.utils import triage_interrupt, user_ask_interrupt, email_modify_interrupt

INTERRUPT_TRIAGE = "classification"
INTERRUPT_ASK_USER = "ask_user"
INTERRUPT_ACK_EMAIL = "ack_email"

INTERRUPT_TAGS = {
    INTERRUPT_TRIAGE: triage_interrupt,
    INTERRUPT_ASK_USER: user_ask_interrupt,
    INTERRUPT_ACK_EMAIL: email_modify_interrupt,
}

class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]


class StateInput(TypedDict):
    email_input: dict


class UserPreferences(BaseModel):
    chain_of_thought: str = Field(description="判断需要添加/更新哪些用户偏好设置（如有需要）。")
    user_preferences: str = Field(description="更新的用户偏好设置")

class SendEmailParam(BaseModel):
    to: str = Field(description="收件人")
    subject: str = Field(description="邮件主题")
    content: str = Field(description="邮件内容")


class AskUserParam(BaseModel):
    content: str = Field(description="询问内容")


class RouterSchema(BaseModel):
    reasoning: str = Field(description="分类背后的逐步推理")
    classification: Literal["ignore", "respond", "notify"] = Field(description="邮件分类")