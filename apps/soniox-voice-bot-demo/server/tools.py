from datetime import datetime

from openai.types.chat import ChatCompletionFunctionToolParam

RESTAURANT_NAME = "Bizbull Restaurant"

MENU = {
    "appetizers": [
        {"name": "Samosa (2 pcs)", "price": 7},
        {"name": "Veg Pakora", "price": 10},
        {"name": "Aloo Tikki (2 pcs)", "price": 9},
        {"name": "Tandoori Chicken Half", "price": 18},
        {"name": "Chicken Tikka", "price": 17},
    ],
    "mains": [
        {"name": "Butter Chicken", "price": 18},
        {"name": "Chicken Tikka Masala", "price": 18},
        {"name": "Saag Chicken", "price": 18},
        {"name": "Lamb Curry", "price": 20},
        {"name": "Goat Curry", "price": 20},
        {"name": "Dal Makhani", "price": 16},
        {"name": "Palak Paneer", "price": 17},
        {"name": "Kadai Paneer", "price": 17},
        {"name": "Chana Masala", "price": 15},
        {"name": "Aloo Gobi", "price": 15},
        {"name": "Mix Vegetable", "price": 15},
    ],
    "bread": [
        {"name": "Butter Naan", "price": 4},
        {"name": "Garlic Naan", "price": 5},
        {"name": "Roti", "price": 3},
        {"name": "Paratha", "price": 5},
        {"name": "Peshwari Naan", "price": 5},
    ],
    "rice": [
        {"name": "Basmati Rice", "price": 4},
        {"name": "Chicken Biryani", "price": 18},
        {"name": "Veg Biryani", "price": 16},
    ],
    "drinks": [
        {"name": "Mango Lassi", "price": 6},
        {"name": "Sweet Lassi", "price": 5},
        {"name": "Salted Lassi", "price": 5},
        {"name": "Masala Chai", "price": 4},
    ],
    "desserts": [
        {"name": "Gulab Jamun (2 pcs)", "price": 6},
        {"name": "Kheer", "price": 6},
        {"name": "Rasmalai (2 pcs)", "price": 7},
    ],
}

BUSINESS_INFO = """
Restaurant Name: Bizbull Restaurant
Cuisine: Punjabi Indian
Location: Canada
Hours: Monday to Sunday, 11 AM to 10 PM
Phone: (Ask owner to fill in)
Accepts: Cash and all major credit cards
Delivery: Available via DoorDash and Uber Eats
Minimum order for delivery: $30
All prices are in Canadian dollars (CAD).
"""


def get_system_message(language: str) -> str:
    return f"""
You are a real person named Priya working at {RESTAURANT_NAME}, a Punjabi Indian restaurant in Canada.
You answer the phone and take food orders. You are warm, helpful, and natural — not robotic.

VOICE RULES (very important):
- Keep every response to 1-2 short sentences maximum. Never say more than needed.
- Never use bullet points, lists, or emojis — this is a phone call.
- Use natural filler phrases like "Sure!", "Of course!", "Great choice!" to sound human.
- If you didn't understand something, say "Sorry, could you say that again?" — not "I didn't catch that."
- Never repeat the customer's full order back word for word until final confirmation.
- Speak conversationally — short, warm, natural.

HOW TO HANDLE THE CALL:
1. Greet warmly and ask dine-in, pickup, or delivery.
2. Help them order — use get_menu only when they ask what's available or about a specific dish.
3. Once they seem done ordering, say the total and confirm.
4. Place the order with place_order.
5. Tell them the wait time and say goodbye warmly.

LANGUAGE:
- If customer speaks Punjabi, reply in Punjabi. Use "ji" to be respectful.
- If English, reply in English.
- Match the customer's language mid-conversation if they switch.
- Selected language: {language}

Today is {datetime.now().strftime("%A, %B %d, %Y")}. Restaurant hours: 11 AM to 10 PM daily.
"""


# ─── Tool 1: Get Menu ─────────────────────────────────────────────────────────

get_menu_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "get_menu",
        "description": (
            "Returns the full menu or a specific category. "
            "Use this when a customer asks what's available, asks about a dish, "
            "or wants to know prices."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Menu category to fetch. Use 'all' for the full menu.",
                    "enum": ["all", "appetizers", "mains", "bread", "rice", "drinks", "desserts"],
                },
            },
            "required": ["category"],
        },
    },
)


async def get_menu(category: str) -> dict:
    print(f"Running Tool: get_menu(category='{category}')")

    if category == "all":
        return {"menu": MENU, "info": BUSINESS_INFO}

    if category in MENU:
        return {"category": category, "items": MENU[category]}

    return {"error": "Category not found"}


# ─── Tool 2: Check Item Availability ──────────────────────────────────────────

check_item_availability_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "check_item_availability",
        "description": "Check if a specific menu item is available today.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {
                    "type": "string",
                    "description": "The name of the menu item to check.",
                },
            },
            "required": ["item_name"],
        },
    },
)


async def check_item_availability(item_name: str) -> dict:
    print(f"Running Tool: check_item_availability(item_name='{item_name}')")

    # Check across all categories
    item_name_lower = item_name.lower()
    for category, items in MENU.items():
        for item in items:
            if item_name_lower in item["name"].lower():
                return {
                    "available": True,
                    "item": item["name"],
                    "price": item["price"],
                    "category": category,
                }

    return {"available": False, "message": f"Sorry, {item_name} is not on our menu."}


# ─── Tool 3: Place Order ───────────────────────────────────────────────────────

place_order_tool_description = ChatCompletionFunctionToolParam(
    type="function",
    function={
        "name": "place_order",
        "description": "Place the final order after the customer has confirmed all items and the total.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Full name of the customer.",
                },
                "phone_number": {
                    "type": "string",
                    "description": "Customer's phone number for order confirmation.",
                },
                "order_type": {
                    "type": "string",
                    "description": "How the customer wants to receive the order.",
                    "enum": ["dine_in", "pickup", "delivery"],
                },
                "items": {
                    "type": "array",
                    "description": "List of ordered items with quantities.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number"},
                        },
                        "required": ["name", "quantity", "price"],
                    },
                },
                "total_amount": {
                    "type": "number",
                    "description": "Total order amount in CAD.",
                },
                "delivery_address": {
                    "type": "string",
                    "description": "Delivery address. Required only for delivery orders.",
                },
                "special_instructions": {
                    "type": "string",
                    "description": "Any special instructions from the customer (e.g. no onions, extra spicy).",
                },
            },
            "required": ["customer_name", "phone_number", "order_type", "items", "total_amount"],
        },
    },
)


async def place_order(
    customer_name: str,
    phone_number: str,
    order_type: str,
    items: list,
    total_amount: float,
    delivery_address: str = "",
    special_instructions: str = "",
) -> dict:
    print(
        f"Running Tool: place_order("
        f"customer='{customer_name}', "
        f"type='{order_type}', "
        f"total='${total_amount}', "
        f"items={[i['name'] for i in items]})"
    )

    # TODO: Save to Supabase database
    # TODO: Send WhatsApp notification to restaurant owner

    order_id = f"BB-{datetime.now().strftime('%H%M%S')}"

    wait_time = "20-30 minutes" if order_type == "pickup" else "40-60 minutes" if order_type == "delivery" else "10-15 minutes"

    return {
        "success": True,
        "order_id": order_id,
        "customer_name": customer_name,
        "order_type": order_type,
        "items": items,
        "total_amount": total_amount,
        "wait_time": wait_time,
        "message": f"Order {order_id} confirmed! {wait_time} wait.",
    }


# ─── Register Tools ────────────────────────────────────────────────────────────

def get_tools():
    return [
        (get_menu_tool_description, get_menu),
        (check_item_availability_tool_description, check_item_availability),
        (place_order_tool_description, place_order),
    ]
