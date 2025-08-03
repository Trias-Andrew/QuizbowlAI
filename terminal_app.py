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
        question = tossup['question_sanitized']
        print(f"Tossup {tossup['number']}:")
        attempted_teams = set()
        idx = 0
        reading_done = False
        final_window_start = None

        while True:
            # Print next word if still reading
            if not reading_done and idx < len(words):
                print(words[idx], end=' ', flush=True)
                idx += 1
                wait_time = self.read_speed
            elif not reading_done:
                print()  # Newline after question
                print("Final chance to buzz! You have 3 seconds...")
                reading_done = True
                final_window_start = time.time()
                wait_time = 3
            else:
                wait_time = max(0, 3 - (time.time() - final_window_start))

            start = time.time()
            buzzed = False
            while time.time() - start < wait_time:
                buzz_type = self.check_for_buzz(question)
                if buzz_type == 1:
                    buzzed = True
                    team = "TeamA"
                    break
                elif buzz_type == 2:
                    buzzed = True
                    team = "TeamB"
                    break                
                time.sleep(0.05)

            if buzzed:
                print("\nBuzz detected!")
                if team not in self.scores or team in attempted_teams:
                    print("Invalid or duplicate buzz. Ignoring.")
                    continue
                if buzz_type == 1:
                    answer = input(f"{team}, your answer: ")
                elif buzz_type == 2:
                    answer = self.ask_llm_player(question)
                buzz_time = 'power' if not reading_done and idx < len(words) // 2 else ('interrupt' if not reading_done else 'normal')
                attempted_teams.add(team)
                result = self.buzz(team, answer, buzz_time=buzz_time, attempted_teams=attempted_teams)
                if result == "correct":
                    return
                if len(attempted_teams) == 2:
                    print("Both teams have buzzed. No more buzzes allowed for this tossup.")
                    break

            # Exit after final window
            if reading_done and (time.time() - final_window_start >= 3 or len(attempted_teams) == 2):
                break

        print(f"No more buzzes. The correct answer was: {tossup['answer_sanitized']}")
        self.tossup_index += 1
    
    def ask_llm_player(self, question):
        response = ollama.chat(model='llama3', messages=[
        {
            'role': 'user',
            'content': f"answer the question: {' '.join(question)}. Only give the answer only",
        }
        ])        
        return response.message.content

    def check_for_buzz(self, question):
        # Check if Enter is pressed (simulate buzz)
        import sys
        import select
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return 1
        if not '0' in self.ask_llm_player(question):
            return 2
        return 0

    def buzz(self, team, answer, buzz_time='normal', attempted_teams=None):
        tossup = self.tossups[self.tossup_index]
        correct = self.check_answer(answer, tossup['answer_sanitized'])
        is_first_attempt = attempted_teams is not None and len(attempted_teams) == 1
        if correct:
            points = 15 if buzz_time == 'power' else 10
            self.scores[team] += points
            self.current_bonus_team = team
            print(f"{team} answered correctly! +{points} points.")
            self.tossup_index += 1
            self.ask_bonus()
            return "correct"
        else:
            # Penalize for both 'power' and 'interrupt' if first attempt
            if buzz_time in ('power', 'interrupt') and is_first_attempt:
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
            if self.current_bonus_team == 'TeamB':
                answer = self.ask_llm_player(part)
            elif self.current_bonus_team == 'TeamA':
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