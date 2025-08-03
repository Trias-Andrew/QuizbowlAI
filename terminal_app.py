import json
import time
import ollama

class QuizbowlGame:
    def __init__(self, tossups, bonuses, read_speed=0.5):
        self.tossups = tossups
        self.bonuses = bonuses
        self.tossup_index = 0
        self.bonus_index = 0
        self.scores = {'TeamA': 0, 'TeamB': 0}
        self.current_bonus_team = None
        self.read_speed = read_speed  # seconds per word
        self.client = ollama.Client()

    # ...existing code...

    def read_tossup(self):
        tossup = self.tossups[self.tossup_index]
        words = tossup['question_sanitized'].split()
        print(f"Tossup {tossup['number']}:")
        buzzed = False
        attempted_teams = set()
        idx = 0
        while idx < len(words):
            print(words[idx], end=' ', flush=True)
            start = time.time()
            while time.time() - start < self.read_speed:
                if self.check_for_buzz():
                    buzzed = True
                    break
                time.sleep(0.05)
            if buzzed:
                print("\nBuzz detected!")
                team = input("Which team buzzed? (TeamA/TeamB): ").strip()
                if team not in self.scores or team in attempted_teams:
                    print("Invalid or duplicate buzz. Ignoring.")
                    buzzed = False
                    continue
                answer = input(f"{team}, your answer: ")
                buzz_time = 'power' if idx < len(words) // 2 else 'interrupt'
                attempted_teams.add(team)
                result = self.buzz(team, answer, buzz_time=buzz_time, attempted_teams=attempted_teams)
                if result == "correct":
                    return
                # If incorrect, continue reading for other team to buzz (if they haven't)
                buzzed = False
                continue
            idx += 1
        print()  # Newline after question
        # After reading, allow buzz from either team if not already attempted
        for team in self.scores:
            if team not in attempted_teams:
                try_buzz = input(f"{team}, do you want to buzz? (y/n): ").strip().lower()
                if try_buzz == 'y':
                    answer = input(f"{team}, your answer: ")
                    attempted_teams.add(team)
                    result = self.buzz(team, answer, buzz_time='normal', attempted_teams=attempted_teams)
                    if result == "correct":
                        return
        # If less than both teams have attempted, wait 3 seconds then reveal answer
        if len(attempted_teams) < 2:
            print("No more buzzes. Revealing answer in 3 seconds...")
            time.sleep(3)
            print(f"The correct answer was: {tossup['answer_sanitized']}")
        else:
            print(f"The correct answer was: {tossup['answer_sanitized']}")
        self.tossup_index += 1
    
    def check_for_buzz(self):
        # Check if Enter is pressed (simulate buzz)
        import sys
        import select
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return True
        return False

    def buzz(self, team, answer, buzz_time='normal', attempted_teams=None):
        tossup = self.tossups[self.tossup_index]
        correct = self.check_answer(answer, tossup['answer_sanitized'])
        if correct:
            points = 15 if buzz_time == 'power' else 10
            self.scores[team] += points
            self.current_bonus_team = team
            print(f"{team} answered correctly! +{points} points.")
            self.tossup_index += 1
            self.ask_bonus()
            return "correct"
        else:
            if buzz_time == 'interrupt':
                self.scores[team] -= 5
                print(f"{team} interrupted incorrectly! -5 points.")
            print(f"{team} answered incorrectly.")
            return "incorrect"

    def ask_bonus(self):
        bonus = self.bonuses[self.bonus_index]
        print(f"Bonus {bonus.get('number', self.bonus_index+1)}: {bonus.get('leadin_sanitized', '')}")
        total_bonus = 0
        for i, part in enumerate(bonus.get('parts_sanitized', [])):
            print(f"Part {i+1}: {part}")
            answer = input(f"{self.current_bonus_team}, your answer: ")
            if self.check_answer(answer, bonus.get('answers_sanitized', [''])[i]):
                value = bonus.get('values', [10]*len(bonus.get('parts_sanitized', [])))[i]
                self.scores[self.current_bonus_team] += value
                total_bonus += value
                print(f"Correct! +{value} points.")
            else:
                print("Incorrect.")
        print(f"Bonus total: {total_bonus} points.")
        self.bonus_index += 1

    def check_answer(self, player_answer, correct_answer):
        response = ollama.chat(model='llama2', messages=[
        {
            'role': 'user',
            'content': f"The groundtruth is '{correct_answer}'. The player answered '{player_answer}'. Is the answer correct? Only print 1 or 0 nothing else. If the player answer is correct according to the groundtruth answer print 1 if not print 0.",
        },
        ])
        print(response.message.content)
        return bool(int(response.message.content))

    def show_scores(self):
        print("Scores:", self.scores)

if __name__ == "__main__":
    with open("tossups_and_bonuses/data.json") as f:
        data = json.load(f)
    print("Welcome to Quizbowl!")
    print("Press Enter at any time during tossup reading to buzz in.")
    print("Type your team name and answer when prompted.")
    print("Type Ctrl+C to exit.\n")
    game = QuizbowlGame(data['tossups'], data['bonuses'], read_speed=0.3)
    try:
        while game.tossup_index < len(game.tossups):
            game.read_tossup()
            game.show_scores()
        print("\nGame over!")
        print("Final scores:")
        game.show_scores()
    except KeyboardInterrupt:
        print("\nGame interrupted.")
        print("Final scores:")
        game.show_scores()