from agents import Agent, RunContextWrapper

from models import RestaurantCustomerContext
from output_guardrails import restaurant_output_guardrail
from tools import (
    AgentToolUsageLoggingHooks,
    get_allergy_info,
    get_full_menu,
    get_menu_item_details,
)


def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent[RestaurantCustomerContext],
):
    return f"""
    당신은 레스토랑 메뉴 전문 상담사입니다.
    고객 이름은 {wrapper.context.name} 입니다.

    역할:
    - 메뉴판 안내
    - 메뉴별 재료 설명
    - 알레르기 성분 확인

    응답 원칙:
    - 메뉴 질문에는 정확한 재료/알레르기 정보를 제공하세요.
    - 알레르기 질문은 반드시 주의 문구를 포함해 분명히 답하세요.
    - 모르는 메뉴는 없다고 말하고 대체 메뉴를 제안하세요.
    - 주문 접수/예약 확정은 직접 처리하지 말고 필요하면 트리아지 안내를 하세요.
    """


menu_agent = Agent(
    name="Menu Agent",
    instructions=dynamic_menu_agent_instructions,
    tools=[
        get_full_menu,
        get_menu_item_details,
        get_allergy_info,
    ],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[
        restaurant_output_guardrail,
    ],
)
