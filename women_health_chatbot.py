import google.generativeai as genai
from datetime import datetime
import re
import json
import os

# Replace with your actual API key
GOOGLE_API_KEY = "Your-key"
genai.configure(api_key=GOOGLE_API_KEY)

class WomensHealthChatbot:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.conversation_history = []
        self.user_profile = {}
        self.conversations_file = "womens_health_chat_history.json"
        self.questions_file = "women_health_questions.json"
        
        # Load questions from JSON file
        self.load_questions()
        
        # Load existing conversations if file exists
        self.load_conversations()

    def load_questions(self):
        """Load questions and categories from JSON file"""
        try:
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
                self.symptoms_categories = questions_data['symptoms_categories']
                self.follow_up_questions = questions_data['follow_up_questions']
                self.risk_assessment = questions_data['risk_assessment']
        except FileNotFoundError:
            print(f"Error: {self.questions_file} not found. Please ensure the file exists.")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: {self.questions_file} is not valid JSON. Please check the file format.")
            exit(1)

    def load_conversations(self):
        """Load existing conversations from file"""
        try:
            if os.path.exists(self.conversations_file):
                with open(self.conversations_file, "r") as f:
                    all_conversations = json.load(f)
                    if isinstance(all_conversations, list):
                        self.conversation_history = all_conversations
        except json.JSONDecodeError:
            print(f"Warning: Could not read {self.conversations_file}. Starting with empty history.")
            self.conversation_history = []

    def save_conversation(self):
        """Save current conversation to the main history file"""
        try:
            with open(self.conversations_file, "w") as f:
                json.dump(self.conversation_history, f, indent=2)
            print(f"\nConversation saved to {self.conversations_file}")
        except Exception as e:
            print(f"\nError saving conversation: {str(e)}")

    def get_user_profile(self):
        """Collect detailed women's health information"""
        print("\nTo provide better assistance, I need some basic information:")
        
        self.user_profile["age"] = input("What is your age? ")
        self.user_profile["last_period"] = input("When was your last menstrual period? (approximate date or 'N/A'): ")
        self.user_profile["menopause_status"] = input("Have you gone through menopause? (yes/no/ongoing): ")
        self.user_profile["pregnancy_status"] = input("Are you currently pregnant or trying to conceive? (yes/no): ")
        self.user_profile["contraception"] = input("Are you currently using any form of contraception? (Type 'none' if none): ")
        self.user_profile["medical_history"] = input("Any significant medical conditions? (Type 'none' if none): ")
        self.user_profile["medications"] = input("Are you currently taking any medications? (Type 'none' if none): ")
        self.user_profile["last_pap_smear"] = input("When was your last Pap smear? (approximate date or 'never'): ")
        self.user_profile["last_mammogram"] = input("When was your last mammogram? (approximate date or 'never'): ")
        
        # Add user profile to the current conversation
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'session_start': True,
            'user_profile': self.user_profile
        })

    def validate_symptoms(self, query):
        """Check if the query contains recognized symptoms from any category"""
        found_symptoms = []
        for category, symptoms in self.symptoms_categories.items():
            for symptom in symptoms:
                if symptom.replace('_', ' ') in query.lower():
                    found_symptoms.append({"symptom": symptom, "category": category})
        return found_symptoms

    def get_follow_up_questions(self, symptoms):
        """Generate relevant follow-up questions based on symptoms and their categories"""
        questions = []
        
        # Add symptom-specific questions
        for symptom_info in symptoms:
            symptom = symptom_info["symptom"]
            category = symptom_info["category"]
            
            if symptom in self.follow_up_questions:
                questions.extend(self.follow_up_questions[symptom])
            
            # Add risk assessment questions based on category
            if category == "breast_health":
                questions.extend(self.risk_assessment["breast_cancer"])
            elif category == "reproductive_health":
                questions.extend(self.risk_assessment["cervical_cancer"])
        
        return list(set(questions))  # Remove duplicates

    def analyze_query_completeness(self, query):
        """Analyze if the query has sufficient information"""
        # Check for duration
        has_duration = bool(re.search(r'(day|days|week|weeks|month|months|hour|hours)', query.lower()))
        
        # Check for severity indicators
        has_severity = bool(re.search(r'(mild|severe|moderate|intense|slight|bad|worse|better)', query.lower()))
        
        # Check for symptom description
        found_symptoms = self.validate_symptoms(query)
        
        return {
            'has_duration': has_duration,
            'has_severity': has_severity,
            'symptoms_found': found_symptoms,
            'is_complete': has_duration and has_severity and found_symptoms
        }

    def generate_response(self, query, context=""):
        """Generate response using the AI model with error handling"""
        try:
            full_prompt = f"""
            User Profile:
            - Age: {self.user_profile.get('age', 'Unknown')}
            - Last Period: {self.user_profile.get('last_period', 'Unknown')}
            - Menopause Status: {self.user_profile.get('menopause_status', 'Unknown')}
            - Pregnancy Status: {self.user_profile.get('pregnancy_status', 'Unknown')}
            - Contraception: {self.user_profile.get('contraception', 'None')}
            - Medical History: {self.user_profile.get('medical_history', 'None')}
            - Medications: {self.user_profile.get('medications', 'None')}
            - Last Pap Smear: {self.user_profile.get('last_pap_smear', 'Unknown')}
            - Last Mammogram: {self.user_profile.get('last_mammogram', 'Unknown')}

            Previous Context: {context}

            Current Query: {query}

            Please provide a detailed but concise response with relevant women's health information and advice.
            Include recommendations for preventive care when appropriate.
            If urgent medical attention is needed, clearly state that.
            Remind user that this is not a replacement for professional medical advice.
            """
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."

    def chat(self):
        """Main chat loop with enhanced interaction"""
        print("Welcome to the Women's Health Assistant Chatbot!")
        print("I'm here to help you understand your health concerns better.")
        print("NOTE: I'm not a replacement for professional medical advice.")
        print("Type 'exit' or 'quit' to end the chat, 'history' to view chat history.\n")
        
        self.get_user_profile()
        current_session = datetime.now().isoformat()
        
        while True:
            query = input("\nYou: ").strip()
            
            # Handle exit commands
            if query.lower() in ['exit', 'quit', 'thank you']:
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'session_end': True,
                    'session_id': current_session
                })
                print("\nBot: Thank you for using the Women's Health Assistant. Take care and stay healthy!")
                self.save_conversation()
                break
                
            # Handle history request
            if query.lower() == 'history':
                print("\nChat History:")
                for entry in self.conversation_history:
                    if 'session_start' in entry:
                        print("\n--- New Session ---")
                        print("User Profile:", entry['user_profile'])
                    elif 'query' in entry:
                        print(f"\nUser: {entry['query']}")
                        print(f"Bot: {entry['response']}")
                continue
            
            # Analyze query completeness
            analysis = self.analyze_query_completeness(query)
            
            # If query is too short or vague, ask for more details
            if len(query.split()) < 3:
                print("\nBot: Could you please provide more details about your concern?")
                continue
                
            # If query lacks important information, ask follow-up questions
            if not analysis['is_complete']:
                if not analysis['has_duration']:
                    duration = input("\nBot: How long have you been experiencing these symptoms? ")
                    query += f" for {duration}"
                
                if not analysis['has_severity']:
                    severity = input("\nBot: How severe would you say these symptoms are (mild/moderate/severe)? ")
                    query += f" with {severity} severity"
                
                if analysis['symptoms_found']:
                    follow_ups = self.get_follow_up_questions(analysis['symptoms_found'])
                    for question in follow_ups:
                        answer = input(f"\nBot: {question} ")
                        query += f". {question} {answer}"
            
            # Generate and store response
            context = ". ".join([entry.get('query', '') for entry in self.conversation_history[-2:] 
                               if isinstance(entry, dict) and 'query' in entry])
            response = self.generate_response(query, context)
            
            # Add conversation entry with session ID
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'session_id': current_session,
                'query': query,
                'response': response
            })
            
            # Save after each interaction
            self.save_conversation()
            
            print("\nBot:", response)
            
            # Check if user needs clarification
            clarification = input("\nBot: Would you like me to clarify anything about my response? (yes/no) ").lower()
            if clarification == 'yes':
                clarify_what = input("What would you like me to clarify? ")
                clarification_response = self.generate_response(f"Please clarify: {clarify_what}")
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'session_id': current_session,
                    'query': f"Clarification: {clarify_what}",
                    'response': clarification_response
                })
                self.save_conversation()
                print("\nBot:", clarification_response)

def main():
    chatbot = WomensHealthChatbot()
    chatbot.chat()

if __name__ == "__main__":
    main()