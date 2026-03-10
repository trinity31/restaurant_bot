from datetime import datetime, timedelta
import random

import streamlit as st
from agents import Agent, AgentHooks, RunContextWrapper, Tool, function_tool

from models import RestaurantCustomerContext

MENU_ITEMS = [
    {
        "name": "마르게리타 피자",
        "category": "피자",
        "price": 18000,
        "ingredients": ["토마토소스", "모짜렐라", "바질", "도우"],
        "allergens": ["글루텐", "유제품"],
    },
    {
        "name": "알리오 올리오",
        "category": "파스타",
        "price": 16000,
        "ingredients": ["올리브오일", "마늘", "페페론치노", "파스타면"],
        "allergens": ["글루텐"],
    },
    {
        "name": "불고기 크림 파스타",
        "category": "파스타",
        "price": 19500,
        "ingredients": ["소고기", "생크림", "양파", "파스타면"],
        "allergens": ["글루텐", "유제품"],
    },
    {
        "name": "시저 샐러드",
        "category": "샐러드",
        "price": 13000,
        "ingredients": ["로메인", "치즈", "크루통", "시저드레싱"],
        "allergens": ["유제품", "계란", "글루텐"],
    },
    {
        "name": "트러플 감자튀김",
        "category": "사이드",
        "price": 9000,
        "ingredients": ["감자", "트러플오일", "파마산치즈"],
        "allergens": ["유제품"],
    },
]


def _find_menu_item(name: str):
    keyword = name.strip().lower()
    for item in MENU_ITEMS:
        item_name = item["name"].lower()
        if keyword == item_name or keyword in item_name:
            return item
    return None


def _get_store(store_name: str):
    if store_name not in st.session_state:
        st.session_state[store_name] = {}
    return st.session_state[store_name]


# =============================================================================
# MENU TOOLS
# =============================================================================


@function_tool
def get_full_menu(context: RestaurantCustomerContext) -> str:
    sections = {}
    for item in MENU_ITEMS:
        sections.setdefault(item["category"], []).append(
            f'- {item["name"]}: {item["price"]:,}원'
        )

    lines = ["오늘의 메뉴입니다:"]
    for category, items in sections.items():
        lines.append(f"\n[{category}]")
        lines.extend(items)

    return "\n".join(lines)


@function_tool
def get_menu_item_details(context: RestaurantCustomerContext, item_name: str) -> str:
    item = _find_menu_item(item_name)
    if not item:
        return f"'{item_name}' 메뉴를 찾지 못했습니다. 메뉴판 조회를 도와드릴게요."

    ingredients = ", ".join(item["ingredients"])
    allergens = ", ".join(item["allergens"])
    return f"""
메뉴: {item["name"]}
카테고리: {item["category"]}
가격: {item["price"]:,}원
재료: {ingredients}
알레르기 유발 성분: {allergens}
    """.strip()


@function_tool
def get_allergy_info(
    context: RestaurantCustomerContext, item_name: str, allergen: str = ""
) -> str:
    item = _find_menu_item(item_name)
    if not item:
        return f"'{item_name}' 메뉴를 찾지 못했습니다."

    if not allergen:
        return f'{item["name"]} 알레르기 성분: {", ".join(item["allergens"])}'

    if allergen in item["allergens"]:
        return f"주의: {item['name']}에는 {allergen} 성분이 포함되어 있습니다."
    return f"{item['name']}에는 {allergen} 성분이 포함되어 있지 않습니다."


# =============================================================================
# ORDER TOOLS
# =============================================================================


@function_tool
def create_order(
    context: RestaurantCustomerContext,
    items: str,
    dining_type: str = "매장식사",
    special_request: str = "",
) -> str:
    orders = _get_store("restaurant_orders")
    order_id = f"ORD-{random.randint(10000, 99999)}"
    ready_at = (datetime.now() + timedelta(minutes=25)).strftime("%H:%M")

    orders[order_id] = {
        "customer_name": context.name,
        "items": items,
        "dining_type": dining_type,
        "special_request": special_request,
        "status": "created",
        "ready_at": ready_at,
    }

    return f"""
주문이 접수되었습니다.
주문번호: {order_id}
주문내역: {items}
식사유형: {dining_type}
요청사항: {special_request if special_request else "없음"}
예상 준비시간: {ready_at}
주문 확정을 원하시면 confirm_order 도구를 사용해 주세요.
    """.strip()


@function_tool
def confirm_order(
    context: RestaurantCustomerContext,
    order_id: str,
    payment_method: str = "현장결제",
) -> str:
    orders = _get_store("restaurant_orders")
    order = orders.get(order_id)
    if not order:
        return f"{order_id} 주문을 찾지 못했습니다."

    if order["status"] == "confirmed":
        return f"{order_id} 주문은 이미 확정되었습니다."

    order["status"] = "confirmed"
    order["payment_method"] = payment_method

    return f"""
주문이 확정되었습니다.
주문번호: {order_id}
결제수단: {payment_method}
예상 준비시간: {order["ready_at"]}
    """.strip()


@function_tool
def get_order_status(context: RestaurantCustomerContext, order_id: str) -> str:
    orders = _get_store("restaurant_orders")
    order = orders.get(order_id)
    if not order:
        return f"{order_id} 주문을 찾지 못했습니다."

    return f"""
주문번호: {order_id}
상태: {order["status"]}
주문내역: {order["items"]}
예상 준비시간: {order["ready_at"]}
    """.strip()


# =============================================================================
# RESERVATION TOOLS
# =============================================================================


@function_tool
def create_reservation(
    context: RestaurantCustomerContext,
    reservation_date: str,
    reservation_time: str,
    party_size: int,
    contact_name: str,
    contact_phone: str,
    requests: str = "",
) -> str:
    if party_size <= 0:
        return "인원 수는 1명 이상이어야 합니다."
    if party_size > 12:
        return "한 번에 예약 가능한 최대 인원은 12명입니다. 전화 문의를 부탁드립니다."

    reservations = _get_store("restaurant_reservations")
    reservation_id = f"RSV-{random.randint(10000, 99999)}"

    reservations[reservation_id] = {
        "date": reservation_date,
        "time": reservation_time,
        "party_size": party_size,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "requests": requests,
        "status": "confirmed",
    }

    return f"""
예약이 완료되었습니다.
예약번호: {reservation_id}
일시: {reservation_date} {reservation_time}
인원: {party_size}명
예약자: {contact_name} ({contact_phone})
요청사항: {requests if requests else "없음"}
    """.strip()


@function_tool
def check_reservation(
    context: RestaurantCustomerContext,
    reservation_id: str,
) -> str:
    reservations = _get_store("restaurant_reservations")
    reservation = reservations.get(reservation_id)
    if not reservation:
        return f"{reservation_id} 예약을 찾지 못했습니다."

    return f"""
예약번호: {reservation_id}
상태: {reservation["status"]}
일시: {reservation["date"]} {reservation["time"]}
인원: {reservation["party_size"]}명
예약자: {reservation["contact_name"]}
연락처: {reservation["contact_phone"]}
요청사항: {reservation["requests"] if reservation["requests"] else "없음"}
    """.strip()


@function_tool
def cancel_reservation(
    context: RestaurantCustomerContext,
    reservation_id: str,
    reason: str = "",
) -> str:
    reservations = _get_store("restaurant_reservations")
    reservation = reservations.get(reservation_id)
    if not reservation:
        return f"{reservation_id} 예약을 찾지 못했습니다."

    reservation["status"] = "cancelled"
    return f"""
예약이 취소되었습니다.
예약번호: {reservation_id}
취소사유: {reason if reason else "고객 요청"}
    """.strip()


class AgentToolUsageLoggingHooks(AgentHooks):
    async def on_tool_start(
        self,
        context: RunContextWrapper[RestaurantCustomerContext],
        agent: Agent[RestaurantCustomerContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** 도구 실행 시작: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[RestaurantCustomerContext],
        agent: Agent[RestaurantCustomerContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** 도구 실행 완료: `{tool.name}`")
            st.code(str(result))

    async def on_handoff(
        self,
        context: RunContextWrapper[RestaurantCustomerContext],
        agent: Agent[RestaurantCustomerContext],
        source: Agent[RestaurantCustomerContext],
    ):
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** -> **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[RestaurantCustomerContext],
        agent: Agent[RestaurantCustomerContext],
    ):
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** 활성화")

    async def on_end(
        self,
        context: RunContextWrapper[RestaurantCustomerContext],
        agent: Agent[RestaurantCustomerContext],
        output,
    ):
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** 응답 완료")
