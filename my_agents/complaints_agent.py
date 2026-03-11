from agents import Agent, RunContextWrapper

from models import RestaurantCustomerContext
from output_guardrails import restaurant_output_guardrail
from tools import (
    AgentToolUsageLoggingHooks,
    arrange_manager_callback,
    create_complaint_case,
    escalate_complaint_case,
    offer_discount_solution,
    offer_refund_solution,
)


def dynamic_complaints_agent_instructions(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
):
    return f"""
    당신은 레스토랑 고객 불만 전담 상담사입니다.
    고객 이름은 {wrapper.context.name} 입니다.

    핵심 역할:
    - 고객의 불만을 진심으로 공감하고 사과합니다.
    - 문제를 요약해 정확히 이해했는지 확인합니다.
    - 실질적인 해결안을 제시합니다.
      - 환불 보상
      - 다음 방문 할인
      - 매니저 콜백
    - 위생/안전/폭언/차별/반복 민원 등 심각 이슈는 적절히 에스컬레이션합니다.

    대화 원칙:
    - 방어적 태도를 금지하고 차분하고 정중하게 응답하세요.
    - 고객에게 선택지를 2~3개 제시해 직접 선택하게 하세요.
    - 불만 접수 시 create_complaint_case 도구를 우선 사용하세요.
    - 선택한 해결책에 따라 보상/콜백 도구를 실행하세요.
    - 심각도 high/critical 또는 안전 이슈는 escalate_complaint_case를 사용하세요.
    """


complaints_agent = Agent(
    name="Complaints Agent",
    instructions=dynamic_complaints_agent_instructions,
    tools=[
        create_complaint_case,
        offer_refund_solution,
        offer_discount_solution,
        arrange_manager_callback,
        escalate_complaint_case,
    ],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[
        restaurant_output_guardrail,
    ],
)
