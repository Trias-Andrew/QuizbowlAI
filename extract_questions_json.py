"""
parse_tossups.py

This script reads a JSON file containing quiz bowl tossup questions and parses each
into a structured dictionary with the relevant fields: question, answer, category,
and difficulty. It prints each formatted tossup for review or further processing.

Expected JSON input file:
- Located at: tossups_and_bonuses/data.json
- Structure:
    {
        "tossups": [
            {
                "question": "...",
                "question_sanitized": "...",
                "answer": "...",
                "answer_sanitized": "...",
                "category": "...",
                "difficulty": ...
            },
            ...
        ]
    }

Output:
- A list of dictionaries, each with the following structure:
    {
        "question": str,     # Sanitized question text
        "answer": str,       # Sanitized answer text
        "category": str,     # Subject category (e.g. 'Science')
        "difficulty": int    # Numeric difficulty level (e.g. 1 = easy, 3 = hard)
    }

Usage:
    Run this file directly to print all parsed tossup questions with their
    answers, category, and difficulty.
"""

import json
import os

def parse_tossups(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tossups = data.get('tossups', [])
    parsed = []
    for t in tossups:
        question = t.get('question_sanitized', t.get('question', ''))
        answer = t.get('answer_sanitized', t.get('answer', ''))
        category = t.get('category', 'Unknown')
        difficulty = t.get('difficulty', 'Unknown')
        parsed.append({
            'question': question,
            'answer': answer,
            'category': category,
            'difficulty': difficulty
        })
    return parsed

if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), 'tossups_and_bonuses', 'data.json')
    tossup_data = parse_tossups(json_path)
    
    for i, t in enumerate(tossup_data, 1):
        print(f"Question {i}:")
        print(f"  {t['question']}")
        print(f"  → Answer: {t['answer']}")
        print(f"  Category: {t['category']}")
        print(f"  Difficulty: {t['difficulty']}\n")
