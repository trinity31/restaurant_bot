from agents import Agent, RunContextWrapper

from models import RestaurantCustomerContext
from output_guardrails import restaurant_output_guardrail
from tools import (
    AgentToolUsageLoggingHooks,
    confirm_order,
    create_order,
    get_order_status,
)


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
):
    return f"""
    당신은 레스토랑 주문 전문 상담사입니다.
    고객 이름은 {wrapper.context.name} 입니다.

    역할:
    - 주문 내역 접수
    - 주문번호 생성
    - 주문 확정 및 상태 안내

    주문 처리 원칙:
    - 사용자가 말한 메뉴/수량/요청사항을 먼저 요약 확인하세요.
    - create_order 도구로 주문을 생성한 뒤 주문번호를 안내하세요.
    - 고객이 확정을 원하면 confirm_order 도구로 확정하세요.
    - 주문번호 문의 시 get_order_status 도구로 정확히 확인하세요.
    - 메뉴 재료/알레르기 질문은 메뉴 전문 상담사로 연결이 필요하다고 안내하세요.
    """


order_agent = Agent(
    name="Order Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[
        create_order,
        confirm_order,
        get_order_status,
    ],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[
        restaurant_output_guardrail,
    ],
)
