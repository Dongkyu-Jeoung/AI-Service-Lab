# check_tokens.py
# --------------------------------------------------
# 문장이 실제로 몇 개의 Token으로 쪼개지는지 확인한다.
# --------------------------------------------------

import tiktoken

# GPT-4 계열 모델이 사용하는 인코딩 방식
encoding = tiktoken.get_encoding("cl100k_base")


def show_tokens(text: str) -> None:
    token_ids = encoding.encode(text)
    tokens_as_text = [encoding.decode([tid]) for tid in token_ids]

    print(f"문장: {text!r}")
    print(f"Token 개수: {len(token_ids)}")
    print(f"Token 조각: {tokens_as_text}")
    print("-" * 60)


if __name__ == "__main__":
    show_tokens("I love ChatGPT")
    show_tokens("ChatGPT는 정말 신기하다")
    show_tokens("나는 오늘 학교에 갔다")
    show_tokens("Hello")