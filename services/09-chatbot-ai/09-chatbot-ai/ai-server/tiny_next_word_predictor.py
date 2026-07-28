# tiny_next_word_predictor.py
# --------------------------------------------------
# "바로 앞 단어를 보고 다음 단어를 예측"하는
# 아주 단순한 장난감 언어 모델 (GPT의 축소판 감각)
# --------------------------------------------------

from collections import defaultdict, Counter
import random

# 학습 데이터 (실제로는 GPT가 인터넷 전체 텍스트로 학습하지만,
# 여기서는 원리를 보여주기 위해 문장 몇 개만 사용한다)
corpus = [
    "오늘 날씨가 정말 좋다",
    "오늘 날씨가 너무 덥다",
    "오늘 날씨가 정말 춥다",
    "오늘 기분이 정말 좋다",
    "내일 날씨가 정말 흐리다",
]

# "앞 단어 -> 다음 단어들" 빈도 세기 (학습 과정)
next_word_counts = defaultdict(Counter)

for sentence in corpus:
    words = sentence.split()
    for i in range(len(words) - 1):
        current_word = words[i]
        next_word = words[i + 1]
        next_word_counts[current_word][next_word] += 1


def predict_next_word(current_word: str) -> str:
    """현재 단어 다음에 올 확률이 가장 높은 단어를 반환한다."""
    candidates = next_word_counts.get(current_word)
    if not candidates:
        return "(학습 데이터에 없는 단어)"

    # 가장 많이 등장한 다음 단어를 선택 (실제 GPT는 확률적으로 선택 - PART 3 Temperature 참고)
    return candidates.most_common(1)[0][0]


def generate_sentence(start_word: str, length: int = 5) -> str:
    """시작 단어부터 다음 단어 예측을 반복해서 문장을 만든다."""
    sentence = [start_word]
    current_word = start_word

    for _ in range(length - 1):
        next_word = predict_next_word(current_word)
        if next_word == "(학습 데이터에 없는 단어)":
            break
        sentence.append(next_word)
        current_word = next_word

    return " ".join(sentence)


if __name__ == "__main__":
    print("=== '오늘' 다음에 올 단어들의 빈도 ===")
    print(dict(next_word_counts["오늘"]))
    print()

    print("=== '날씨가' 다음 예측 ===")
    print(predict_next_word("날씨가"))
    print()

    print("=== 문장 생성 (다음 단어 예측 반복) ===")
    print(generate_sentence("오늘", length=4))