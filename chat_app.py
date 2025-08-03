
import ollama

def chat():
    client = ollama.Client()
    system_prompt = "You are a quizbowl bot you should ask questions and check if use answers are correct or wrong and let them know and if correct " \
                    "you should let them know the correct answer and then ask another question in a new line."
        # Initialize messages with system prompt
    messages = [{'role': 'system', 'content': system_prompt}]
    
    print("Welcome to quizball bot (type 'quit' to exit)")
    print("Let me know when you're ready to start!")
    print("-" * 40)

    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'quit':
            break        
        # Add user message to history
        messages.append({'role': 'user', 'content': user_input})
        
        print("Bot: ", end='')
        
        # Stream the response with full conversation history
        response_content = ""
        for chunk in client.chat(model='llama2', messages=messages, stream=True):
            content = chunk['message']['content']
            print(content, end='', flush=True)
            response_content += content

        # Add assistant response to history
        messages.append({'role': 'assistant', 'content': response_content})
        
        print()  # New line after response

if __name__ == "__main__":
    chat()