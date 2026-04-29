from pydantic import BaseModel

class Drawing(BaseModel):
    user_id: int | None = None
    Base64_drawing: str
    timer: int
    current_word: str
    ai_results: dict | None = None

def get_state_game(drawing : Drawing):
    current_word_percentage = drawing.ai_results.get(drawing.current_word, 0)
    if not current_word_percentage:
        return False
    if drawing.timer >= 60:
        return current_word_percentage >= 90
    elif 30 <= drawing.timer < 60:
        return current_word_percentage >= 85
    else:
        return current_word_percentage >= 75