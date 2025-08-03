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

    def read_tossup(self):
        tossup = self.tossups[self.tossup_index]
        words = tossup['question_sanitized'].split()
        print(f"Tossup {tossup['number']}:")
        buzzed = False
        for idx, word in enumerate(words):
            print(word, end=' ', flush=True)
            start = time.time()
            # Wait for read_speed seconds or until Enter is pressed
            while time.time() - start < self.read_speed:
                # Non-blocking buzz check
                if self.check_for_buzz():
                    buzzed = True
                    break
                time.sleep(0.05)
            if buzzed:
                print("\nBuzz detected!")
                team = input("Which team buzzed? (TeamA/TeamB): ").strip()
                answer = input(f"{team}, your answer: ")
                buzz_time = 'power' if idx < len(words) // 2 else 'interrupt'
                self.buzz(team, answer, buzz_time=buzz_time)
                return
        print()  # Newline after question
        # After reading, allow buzz from either team
        team = input("Anyone want to buzz? (TeamA/TeamB or Enter to skip): ").strip()
        if team in self.scores:
            answer = input(f"{team}, your answer: ")
            self.buzz(team, answer, buzz_time='normal')
        else:
            print("No buzz. Moving to next tossup.")
            self.tossup_index += 1

    def check_for_buzz(self):
        # Check if Enter is pressed (simulate buzz)
        import sys
        import select
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return True
        return False

    def buzz(self, team, answer, buzz_time='normal'):
        tossup = self.tossups[self.tossup_index]
        correct = self.check_answer(answer, tossup['answer_sanitized'])
        if correct:
            points = 15 if buzz_time == 'power' else 10
            self.scores[team] += points
            self.current_bonus_team = team
            print(f"{team} answered correctly! +{points} points.")
            self.tossup_index += 1
            self.ask_bonus()
        else:
            if buzz_time == 'interrupt':
                self.scores[team] -= 5
                print(f"{team} interrupted incorrectly! -5 points.")
            print(f"{team} answered incorrectly.")
            # Allow other team to buzz after incorrect interrupt
            other_team = 'TeamB' if team == 'TeamA' else 'TeamA'
            answer = input(f"{other_team}, your answer (or Enter to skip): ")
            if answer.strip():
                self.buzz(other_team, answer, buzz_time='normal')
            else:
                self.tossup_index += 1

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
        while True:
            response = ollama.chat(model='llama2', messages=[
                {
                    'role': 'user',
                    'content': f"The groundtruth is '{correct_answer}'. The player answered '{player_answer}'. Is the answer correct? Only print 0 or 1 nothing else. If the player answer is correct according to the groundtruth answer print 1 if wrong print 0.",
                },
            ])
            content = response.message.content.strip()
            #print(content)
            try:
                return bool(int(content))
            except ValueError:
                print("Response was not an integer. Retrying...")

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