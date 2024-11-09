import json
from datetime import datetime
import google.generativeai as genai
from typing import List, Dict, Any

class SymptomAnalyzer:
    def __init__(self, api_key: str):
        """Initialize Gemini Pro API and configure the model."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.analysis_results = []
    
    def extract_symptoms(self, query: str) -> Dict[str, Any]:
        """Extract symptoms and their details from the query using Gemini Pro."""
        prompt = f"""
        Analyze this medical query and return ONLY a JSON object with the following format:
        {{
            "symptoms": "list main symptoms here",
            "severity": "describe severity here",
            "duration": "describe duration here"
        }}

        Query: {query}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove any markdown code block indicators if present
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
                
            response_text = response_text.strip()
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                # Validate required keys
                required_keys = {'symptoms', 'severity', 'duration'}
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required keys in response")
                return result
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {response_text}")
                # Return a default structure if parsing fails
                return {
                    "symptoms": "parsing error",
                    "severity": "unknown",
                    "duration": "unknown"
                }
                
        except Exception as e:
            print(f"Error in extract_symptoms: {e}")
            return {
                "symptoms": "error",
                "severity": "unknown",
                "duration": "unknown"
            }
    
    def get_diagnosis(self, symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """Get diagnosis and recommendations using Gemini Pro."""
        prompt = f"""
        Analyze these symptoms and return ONLY a JSON object with the following format:
        {{
            "diagnoses": "list possible diagnoses here",
            "recommendations": "list recommended actions here"
        }}

        Symptoms details:
        - Symptoms: {symptoms['symptoms']}
        - Severity: {symptoms['severity']}
        - Duration: {symptoms['duration']}
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove any markdown code block indicators if present
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
                
            response_text = response_text.strip()
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                # Validate required keys
                required_keys = {'diagnoses', 'recommendations'}
                if not all(key in result for key in required_keys):
                    raise ValueError("Missing required keys in response")
                return result
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {response_text}")
                # Return a default structure if parsing fails
                return {
                    "diagnoses": "parsing error",
                    "recommendations": "unable to provide recommendations"
                }
                
        except Exception as e:
            print(f"Error in get_diagnosis: {e}")
            return {
                "diagnoses": "error",
                "recommendations": "error"
            }

def process_chat_history(file_path: str, analyzer: SymptomAnalyzer, output_file: str):
    """Process the chat history and save analysis results to a JSON file."""
    analysis_results = []
    
    try:
        # Read input chat history
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        current_session = None
        current_user_age = None
        
        for entry in data:
            if 'session_start' in entry and entry['session_start']:
                current_session = entry['timestamp']
                current_user_age = entry['user_profile']['age']
                
            elif 'query' in entry and current_session:
                print(f"Processing query: {entry['query'][:100]}...")  # Print first 100 chars of query
                
                # Analyze symptoms using Gemini Pro
                symptoms = analyzer.extract_symptoms(entry['query'])
                print(f"Extracted symptoms: {symptoms}")
                
                diagnosis = analyzer.get_diagnosis(symptoms)
                print(f"Generated diagnosis: {diagnosis}")
                
                # Create analysis entry
                analysis_entry = {
                    'timestamp': current_session,
                    'user_age': current_user_age,
                    'symptoms': symptoms['symptoms'],
                    'severity': symptoms['severity'],
                    'duration': symptoms['duration'],
                    'diagnosis': diagnosis['diagnoses'],
                    'recommendations': diagnosis['recommendations']
                }
                
                analysis_results.append(analysis_entry)
        
        # Write results to JSON file
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2)
            
        print(f"Successfully processed {len(analysis_results)} entries")
            
    except Exception as e:
        print(f"Error processing file: {e}")
        raise

def main():
    # Gemini API configuration
    API_KEY = "your-key-nikhil-boss"
    
    try:
        # Create analyzer instance
        analyzer = SymptomAnalyzer(API_KEY)
        
        # Process the chat history and save results
        process_chat_history(
            'womens_health_chat_history.json',
            analyzer,
            'symptom_analysis_results.json'
        )
        
        print("Analysis complete. Results saved to symptom_analysis_results.json")
            
    except Exception as e:
        print(f"Error in main execution: {e}")
        print("Please make sure:")
        print("1. Your API key is correct")
        print("2. The input file exists and is valid JSON")
        print("3. You have internet connection for the API calls")

if __name__ == "__main__":
    main()