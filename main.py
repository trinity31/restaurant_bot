import asyncio

import dotenv
import streamlit as st
from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)

from models import RestaurantCustomerContext
from my_agents.triage_agent import triage_agent

dotenv.load_dotenv()

st.set_page_config(page_title="Restaurant Bot", page_icon="🍽️")
st.title("Restaurant Bot")

customer_context = RestaurantCustomerContext(
    customer_id=1,
    name="Trinity",
    phone="010-1234-5678",
    preferred_language="ko",
)


HANDOFF_MESSAGES = {
    "Menu Agent": "메뉴 전문가에게 연결합니다...",
    "Order Agent": "주문 전문가에게 연결합니다...",
    "Reservation Agent": "예약 전문가에게 연결합니다...",
    "Complaints Agent": "불만 해결 전문가에게 연결합니다...",
}


def handoff_message(agent_name: str) -> str:
    return HANDOFF_MESSAGES.get(agent_name, f"{agent_name}에게 연결합니다...")


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "restaurant-bot-memory.db",
    )
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" not in message:
            continue

        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            elif message["type"] == "message":
                st.write(message["content"][0]["text"].replace("$", "\\$"))


asyncio.run(paint_history())


async def run_agent(message: str):
    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        response = ""
        active_agent_name = triage_agent.name

        try:
            stream = Runner.run_streamed(
                triage_agent,
                message,
                session=session,
                context=customer_context,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))
                elif event.type == "agent_updated_stream_event":
                    if active_agent_name != event.new_agent.name:
                        st.info(handoff_message(event.new_agent.name))
                        active_agent_name = event.new_agent.name
                        text_placeholder = st.empty()
                        response = ""
        except InputGuardrailTripwireTriggered:
            st.write(
                "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. "
                "메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요."
            )
        except OutputGuardrailTripwireTriggered:
            text_placeholder.empty()
            st.write("해당 질문에 대한 답변은 표시할 수 없습니다.")


message = st.chat_input("메뉴, 주문, 예약, 불만 상담 요청을 입력하세요.")
if message:
    with st.chat_message("user"):
        st.write(message)
    asyncio.run(run_agent(message))


with st.sidebar:
    st.subheader("세션")
    reset = st.button("대화 메모리 초기화")
    if reset:
        asyncio.run(session.clear_session())
        st.success("메모리를 초기화했습니다.")
