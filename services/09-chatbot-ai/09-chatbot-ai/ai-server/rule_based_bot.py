# rule_based_bot.py
# --------------------------------------------------
# 규칙 기반(if-else) 챗봇: 2020년 이전까지 흔했던 방식
# --------------------------------------------------

def rule_based_reply(user_input: str) -> str:
    text = user_input.strip().lower()

    if "환불" in text:
        return "환불은 구매일로부터 7일 이내에 가능합니다."
    elif "배송" in text:
        return "배송은 평균 2~3일 소요됩니다."
    elif "영업시간" in text:
        return "영업시간은 평일 오전 9시부터 오후 6시까지입니다."
    else:
        return "죄송합니다. 이해하지 못했습니다. 다른 방식으로 질문해 주세요."


if __name__ == "__main__":
    test_questions = [
        "환불 어떻게 해요?",
        "배송 얼마나 걸려요?",
        "영업시간이 어떻게 되나요?",
        "혹시 결제 취소하려면 돈은 언제 돌려받을 수 있나요?",  # <- '환불'이라는 단어가 없음
    ]

    for q in test_questions:
        print(f"Q: {q}")
        print(f"A: {rule_based_reply(q)}")
        print("-" * 50)