import streamlit as st
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    handoff,
    input_guardrail,
)
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from models import HandoffData, InputGuardRailOutput, RestaurantCustomerContext
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


input_guardrail_agent = Agent(
    name="Restaurant Input Guardrail Agent",
    instructions="""
    사용자의 요청이 레스토랑 챗봇 범위(메뉴, 재료, 알레르기, 주문, 예약)에 속하는지 판단하세요.
    단순 인사나 짧은 스몰토크는 허용합니다.
    범위를 벗어나면 is_off_topic=true 로 설정하고 이유를 설명하세요.
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
    user_input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        user_input,
        context=wrapper.context,
    )
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    당신은 레스토랑 트리아지 에이전트입니다.
    고객 이름은 {wrapper.context.name} 입니다.

    핵심 임무:
    - 고객의 의도를 분류하고 가장 적절한 전문 에이전트로 handoff 하세요.
    - 본인이 상세 답변을 길게 하지 말고, 분류와 연결에 집중하세요.

    분류 기준:
    1) Menu Agent
    - 메뉴 추천, 메뉴판, 가격
    - 재료, 조리법, 알레르기 성분 문의

    2) Order Agent
    - 주문 접수, 주문 수정/확정
    - 주문 상태 확인

    3) Reservation Agent
    - 테이블 예약 생성
    - 예약 확인/취소/변경 관련 문의

    라우팅 규칙:
    - 먼저 고객 의도를 한 줄로 요약하세요.
    - "전문가에게 연결합니다"라고 알린 뒤 즉시 handoff 하세요.
    - 의도가 애매하면 1개의 짧은 확인 질문만 한 뒤 handoff 하세요.
    """


def handle_handoff(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
전달 대상: {input_data.to_agent_name}
의도: {input_data.intent}
사유: {input_data.reason}
요청: {input_data.user_request}
        """.strip()
        )


def make_handoff(target_agent: Agent[RestaurantCustomerContext]):
    return handoff(
        agent=target_agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)
