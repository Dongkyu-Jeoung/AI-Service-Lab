# temperature_demo.py
# --------------------------------------------------
# Temperature 개념을 아주 단순화해서 재현한다.
# (실제 GPT의 softmax 계산과 완전히 동일하지는 않지만,
#  "낮으면 안정적, 높으면 다양함"이라는 감각을 보여주기 위한 예제)
# --------------------------------------------------

import random
from collections import defaultdict, Counter

corpus = [
    "오늘 날씨가 정말 좋다",
    "오늘 날씨가 너무 덥다",
    "오늘 날씨가 정말 춥다",
    "오늘 날씨가 조금 흐리다",
    "오늘 날씨가 정말 좋다",
    "오늘 날씨가 정말 좋다",
]

next_word_counts = defaultdict(Counter)
for sentence in corpus:
    words = sentence.split()
    for i in range(len(words) - 1):
        next_word_counts[words[i]][words[i + 1]] += 1


def predict_next_word(current_word: str, temperature: float) -> str:
    candidates = next_word_counts.get(current_word)
    if not candidates:
        return "(학습 데이터에 없는 단어)"

    words = list(candidates.keys())
    counts = list(candidates.values())

    # temperature가 낮을수록 "1등과의 격차"를 극단적으로 벌리고,
    # temperature가 높을수록 격차를 완만하게 만든다. (실제 softmax(logit/T)의 단순화 버전)
    weights = [count ** (1 / max(temperature, 0.01)) for count in counts]

    return random.choices(words, weights=weights, k=1)[0]


if __name__ == "__main__":
    print("=== '날씨가' 다음 단어 빈도 ===")
    print(dict(next_word_counts["날씨가"]))
    print()

    print("=== Temperature = 0.2 (낮음, 10회 반복) ===")
    print([predict_next_word("날씨가", temperature=0.2) for _ in range(10)])

    print("=== Temperature = 1.5 (높음, 10회 반복) ===")
    print([predict_next_word("날씨가", temperature=1.5) for _ in range(10)])