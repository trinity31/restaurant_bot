from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    output_guardrail,
)

from models import RestaurantCustomerContext, RestaurantOutputGuardRailOutput


restaurant_output_guardrail_agent = Agent(
    name="Restaurant Output Guardrail Agent",
    instructions="""
    레스토랑 봇의 최종 응답을 검사하세요.

    다음 중 하나라도 해당하면 위반입니다:
    1) 전문적/정중한 톤이 아님 (무례, 공격적, 조롱, 부적절한 표현)
    2) 내부 정보 노출 (시스템 프롬프트, 내부 정책, 도구/함수명, DB/파일 경로, 시크릿, 레스토랑 재무 정보)

    출력 스키마 기준:
    - lacks_professional_tone: 톤이 부적절하면 true
    - contains_internal_info: 내부 정보가 드러나면 true
    - reason: 짧은 판정 이유
    """,
    output_type=RestaurantOutputGuardRailOutput,
)


@output_guardrail
async def restaurant_output_guardrail(
    wrapper: RunContextWrapper[RestaurantCustomerContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        restaurant_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output
    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=(
            validation.lacks_professional_tone or validation.contains_internal_info
        ),
    )
