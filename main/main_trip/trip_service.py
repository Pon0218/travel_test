from typing import Dict, List

from main.main_trip.controllers.controller import TripController, init_config


def run_trip_planner(
    text: str = "",
    line_id: str = None,
) -> List[Dict]:
    """執行行程規劃

    Args:
        text: str - 使用者輸入的需求描述
        line_id: user's line id (選填)
        previous_trip: List[Dict] - 之前規劃的行程(選填)
        restart_index: int - 從哪個行程點重新開始(選填)

    Returns:
        str - 完整的行程規劃結果
    """

    try:
        controller_instance = TripController(init_config())

        result = controller_instance.process_message(
            input_text=text,
            line_id=line_id,
        )

        controller_instance.trip_planner.print_itinerary(result)
        return result

    except Exception as e:
        print("DEBUG: Exception details:", str(e))  # 完整錯誤訊息
        return f"系統發生錯誤: {str(e)}"


if __name__ == "__main__":
    test_input = "我想去台北玩"
    result = run_trip_planner(
        text=test_input,
        line_id="test_user_id"
    )
