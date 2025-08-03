import json
import os

def extract_tossup_questions(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    tossups = data.get('tossups', [])
    questions = [tossup.get('question_sanitized', tossup.get('question', '')) for tossup in tossups]
    return questions

if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), 'tossups_and_bonuses', 'data.json')
    questions = extract_tossup_questions(json_path)
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}\n")
