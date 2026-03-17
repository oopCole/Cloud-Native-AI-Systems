from typing import List, Dict


def normalize_scores(scores: List[int]) -> List[int]:
    """
    Return a new list where each score is clamped to the range [0, 100].
    Example:
    [120, -4, 90] -> [100, 0, 90]
    """
    result: List[int] = []
    for s in scores:
        if s < 0:
            result.append(0)
        elif s > 100:
            result.append(100)
        else:
            result.append(s)
    return result


def letter_grades(scores: List[int]) -> List[str]:
    """
    Convert numeric scores to letter grades using this scale:
    A: 90-100
    B: 80-89
    C: 70-79
    D: 60-69
    F: 0-59
    Notes:
    - First call normalize_scores(scores)
    - Return a list of letters with the same length as scores
    """
    normalized = normalize_scores(scores)
    letters: List[str] = []
    for s in normalized:
        if s >= 90:
            letters.append("A")
        elif s >= 80:
            letters.append("B")
        elif s >= 70:
            letters.append("C")
        elif s >= 60:
            letters.append("D")
        else:
            letters.append("F")
    return letters


def grade_histogram(grades: List[str]) -> Dict[str, int]:
    """
    Return a dictionary mapping each letter in {"A","B","C","D","F"} to its count.
    Example:
    ["A","A","C"] -> {"A":2,"B":0,"C":1,"D":0,"F":0}
    """
    h: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for g in grades:
        if g in h:
            h[g] += 1
    return h
