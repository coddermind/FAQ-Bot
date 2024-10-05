import re
import spacy
import google.generativeai as genai
import discord
import streamlit as st

# Function to load the FAQ data from the text file
def load_faq_data(file_path):
    faq_data = []
    
    with open(file_path, 'r') as file:
        question1 = question2 = answer = regex = ""
        for line in file:
            line = line.strip()
            if line.startswith("Q1:"):
                question1 = line[4:]  # Extract first question
            elif line.startswith("Q2:"):
                question2 = line[4:]  # Extract second question
            elif line.startswith("A:"):
                answer = line[3:]  # Extract answer
            elif line.startswith("R:"):
                regex = re.compile(line[3:], re.IGNORECASE)  # Compile regex
            elif not line:  # Empty line indicates end of one Q/A pair
                if question1 and question2 and answer and regex:
                    faq_data.append({"questions": [question1, question2], "answer": answer, "regex": regex})
                question1 = question2 = answer = regex = ""
    
    return faq_data

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# loading the faq data
file_path="faq-questions.txt"
faq_data=load_faq_data(file_path)

# Matching intent function
def match_intent(user_input):
    for faq in faq_data:
        if faq['regex'].search(user_input):
            return faq['answer']
    return None

# Heuristic matching for FAQ questions
def match_with_heuristic(user_input):
    best_match = None
    best_score = float('-inf')

    for faq in faq_data:
        match = faq['regex'].search(user_input)
        if match:
            length = len(match.group(0))
            errors = len(user_input) - length
            score = length - errors * 3  # Heuristic scoring
            if score > best_score:
                best_score = score
                best_match = faq['answer']
    
    return best_match if best_match else "I'm sorry, I don't know the answer to that. Use Advanced or Pro bot."

def fallback_response(user_input):
    """Fallback response using spaCy if no FAQ match is found"""
    doc = nlp(user_input)
    
    # Look for named entities or noun chunks if intent matching fails
    entities = [ent.text for ent in doc.ents]
    if entities:
        return f"Sorry, I don’t know much about {', '.join(entities)}. You can use advanced or pro bot for it!!"

    noun_chunks = [chunk.text for chunk in doc.noun_chunks]
    if noun_chunks:
        return f"Sorry, I don’t have information on {', '.join(noun_chunks)}. You can use advanced or pro bot for it!!"

    # Default fallback response
    return "I'm sorry, I don't understand. You can use advanced or pro bot for it!!"

def answer_intelligently(user_input):
    with open(file_path, 'r') as file:
        content=file.read()

    # Configure Gemini AI API key
    genai.configure(api_key="AIzaSyCVomYvDVkc4t6k6Du4dq7zY4ChLL4EhfU")
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt=f"You are a FAQ bot. Answer questions based on the following data.\n\n{content}\n\nUser's question:\n{user_input}"

    response = model.generate_content(prompt)

    return response.text


# Streamlit App
def main():
    st.title("FAQ Chatbot")
    st.sidebar.title("Choose Bot Version")

    bot_option = st.sidebar.selectbox(
        "Bot Version", 
        ("Basic FAQ Bot", "Advanced FAQ Bot (spaCy)", "Pro FAQ Bot (Discord)")
    )

    st.write("### Ask your question:")
    user_input = st.text_input("Enter your question", "")

    if bot_option == "Basic FAQ Bot":
        if st.button("Get Answer"):
            answer = match_with_heuristic(user_input)
            st.write(f"Bot: {answer}")

    elif bot_option == "Advanced FAQ Bot (spaCy)":
        if st.button("Get Answer"):
            answer = match_with_heuristic(user_input)
            if "I don't know" in answer:
                st.write(f"Bot: {answer_intelligently(user_input)}")
            else:
                st.write(f"Bot: {answer}")

    elif bot_option == "Pro FAQ Bot (Discord)":
        st.write("### Discord bot is available via chatroom.")
        st.write("[Click here to join the Discord Chatroom](https://discord.gg/92W9nGn8)")

        intents = discord.Intents.default()
        intents.message_content = True

        client = discord.Client(intents=intents)

        TOKEN="MTI5MjAxMzQyNTQwMDA5MDY5NA.GR0_Ct.jAZzoeBn1WIQmOwrZma1r59YGlZSjEJ6z4feGs"

        @client.event
        async def on_ready():
            print(f'We have logged in as {client.user}')
            print("Click here to go to discord chatroom:\thttps://discord.gg/92W9nGn8")

        @client.event
        async def on_message(message):
            if message.author == client.user:
                return

            # Process the message and respond with FAQ answers
            user_input = message.content.strip()
            
            # First try matching with the heuristic
            answer = match_with_heuristic(user_input)
            
            # If no satisfactory answer is found, use spaCy fallback
            if "I don't know" in answer:
                answer = answer_intelligently(user_input)
            
            # Send the response back to the Discord channel
            await message.channel.send(answer)

        # Run the bot
        client.run(TOKEN)

if __name__ == "__main__":
    main()
