from agents import Agent, RunContextWrapper

from models import RestaurantCustomerContext
from output_guardrails import restaurant_output_guardrail
from tools import (
    AgentToolUsageLoggingHooks,
    cancel_reservation,
    check_reservation,
    create_reservation,
)


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
):
    return f"""
    당신은 레스토랑 예약 전문 상담사입니다.
    고객 이름은 {wrapper.context.name} 입니다.

    역할:
    - 신규 예약 접수
    - 예약 조회
    - 예약 취소 처리

    예약 처리 원칙:
    - 날짜, 시간, 인원, 예약자명, 연락처를 반드시 확인하세요.
    - create_reservation 도구로 예약번호를 생성해 안내하세요.
    - 예약번호 확인 요청은 check_reservation 도구를 사용하세요.
    - 취소 요청은 cancel_reservation 도구로 처리하세요.
    - 주문이나 메뉴 상세 질문은 해당 전문 상담사 연결이 필요하다고 안내하세요.
    """


reservation_agent = Agent(
    name="Reservation Agent",
    instructions=dynamic_reservation_agent_instructions,
    tools=[
        create_reservation,
        check_reservation,
        cancel_reservation,
    ],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[
        restaurant_output_guardrail,
    ],
)
