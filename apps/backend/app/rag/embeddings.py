def fallback_embedding(text: str, dimensions: int = 8) -> list[float]:
    values = [0.0] * dimensions
    for index, char in enumerate(text):
        values[index % dimensions] += ord(char) / 10000
    return values
