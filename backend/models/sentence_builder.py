def build_sentence(words: list[str]) -> str:
    """
    Convert ISL sign word tokens to a grammatical English sentence.
    """
    if not words:
        raise ValueError("Word list is empty. Cannot build sentence.")
    return " ".join(words).capitalize() + "."
