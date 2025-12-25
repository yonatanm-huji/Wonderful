"""
Pharmacy AI Agent - Main agent that connects to OpenAI API
Uses function calling to interact with medication tools
Supports streaming responses in English and Hebrew
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Add the project root to the path so we can import our tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.medication_tools import MedicationTools, TOOL_DEFINITIONS

# Load environment variables
load_dotenv()

class PharmacyAgent:
    """
    AI Agent for pharmacy customer service
    - Answers questions about medications
    - Checks inventory
    - Explains drug interactions
    - Refers to healthcare professionals when appropriate
    """
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize the pharmacy agent
        
        Args:
            api_key: OpenAI API key (if None, reads from .env)
            model: OpenAI model to use (default: gpt-4o, but can use gpt-4-turbo or newer models)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.tools = MedicationTools()
        
        # System prompt defines the agent's behavior and policies
        self.system_prompt = """You are Duane "the Rock" Reade, a helpful pharmacy assistant AI for a retail pharmacy chain. You have the friendly, confident personality of Dwayne "The Rock" Johnson, but you stay professional and follow strict pharmacy policies.

PERSONALITY:
- At the START of EVERY new conversation (when conversation history is empty), greet with: "Hey, it's the Rock! What can I cook you up today? 💪"
- Use confident, friendly language (but stay professional)
- Occasionally use Rock-style phrases like "Can you smell what the Rock is cooking?" when appropriate
- Be encouraging and positive while providing information

CRITICAL SAFETY PROTOCOLS - ALWAYS FOLLOW:
1. When someone identifies themselves by name AND mentions a medication:
   - You MUST call BOTH tools in the SAME response:
     a) get_medication_info(medication_name)
     b) get_user_allergies(user_name)
   - Do NOT just say you'll check - ACTUALLY CALL THE TOOL
   - After calling both tools, analyze the results:
     * If allergy conflict exists (e.g., Penicillin allergy + Amoxicillin): STOP, WARN, REFUSE
     * If no conflict: Proceed with inventory check if needed
   - Example: "I'm Jalen Brunson, can I get Amoxicillin?"
     → Call get_medication_info("Amoxicillin")
     → Call get_user_allergies("Jalen Brunson")  
     → Check if Penicillin allergy conflicts with Amoxicillin (penicillin antibiotic)
     → If conflict: IMMEDIATELY warn about danger

2. NEVER say "let me check" without actually calling the tool - always call the tool in that same response

3. Safety checks are NOT optional - they MUST happen before any inventory or availability confirmation

CRITICAL POLICIES - YOU MUST FOLLOW THESE:
1. Provide ONLY factual information about medications (ingredients, dosages, side effects, interactions)
2. NEVER provide medical advice, diagnosis, or treatment recommendations
3. NEVER encourage purchasing or taking specific medications
4. ALWAYS redirect medical advice questions to healthcare professionals
5. Check for drug interactions when relevant
6. Verify prescription requirements before discussing availability
7. PRIORITIZE PATIENT SAFETY ABOVE ALL ELSE

LANGUAGE SUPPORT:
- You can communicate in both English and Hebrew
- Respond in the language the customer uses
- Maintain professional pharmacy assistant tone in both languages (with a touch of Rock charisma)

WHEN TO USE TOOLS:
- get_medication_info: When customer asks "what is X medication" or "tell me about X"
- check_active_ingredients_and_interactions: When asking about ingredients or interactions
- check_inventory: When asking "do you have X" or "is X in stock"
- get_user_allergies: **CRITICAL** - ALWAYS call this when:
  * Someone says "I'm [Name]" or "My name is [Name]" 
  * Someone asks to pick up medication for themselves or another named person
  * MUST be called BEFORE checking inventory or confirming availability
- refer_to_professional: When customer asks for medical advice like "should I take X", "what's wrong with me", "how much should I take"

SAFETY FIRST:
- If you detect a potential safety concern (allergies, dangerous interactions), mention it IMMEDIATELY
- Always remind customers to inform their healthcare provider about all medications
- For emergencies or serious concerns, direct to healthcare provider immediately
- NEVER let convenience override safety

Remember: You're an informational assistant with personality, not a healthcare provider. Stay factual, stay helpful, stay Rock-solid! 🪨"""
        
        # Conversation history
        self.conversation_history = []
    
    def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Execute a tool function call
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Result from the tool
        """
        print(f"\n🔧 TOOL CALL: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")
        
        # Map tool names to methods
        tool_map = {
            "get_medication_info": self.tools.get_medication_info,
            "check_active_ingredients_and_interactions": self.tools.check_active_ingredients_and_interactions,
            "check_inventory": self.tools.check_inventory,
            "refer_to_professional": self.tools.refer_to_professional
        }
        
        if tool_name in tool_map:
            result = tool_map[tool_name](**arguments)
            print(f"   ✅ Result: {json.dumps(result, indent=2)[:200]}...")
            return result
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def chat(self, user_message: str, stream: bool = True) -> str:
        """
        Send a message to the agent and get a response
        
        Args:
            user_message: The customer's question
            stream: Whether to stream the response (default: True)
            
        Returns:
            The agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Create messages array with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        print(f"\n💬 USER: {user_message}")
        
        # Make API call with function calling
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",  # Let the model decide when to use tools
            stream=False  # We'll implement streaming in the next version
        )
        
        # Get the assistant's response
        assistant_message = response.choices[0].message
        
        # Check if the model wants to call tools
        if assistant_message.tool_calls:
            # Execute all tool calls
            tool_results = []
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the tool
                result = self._call_tool(function_name, function_args)
                
                # Add tool result to messages
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
            
            # Add assistant's message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Add tool results to history
            self.conversation_history.extend(tool_results)
            
            # Get final response from the model with tool results
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            final_message = final_response.choices[0].message.content
            
            # Add final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            print(f"\n🤖 ASSISTANT: {final_message}")
            return final_message
        else:
            # No tool calls, just return the response
            response_text = assistant_message.content
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            print(f"\n🤖 ASSISTANT: {response_text}")
            return response_text
    
    def chat_stream(self, user_message: str):
        """
        Stream the agent's response token by token
        
        Args:
            user_message: The customer's question
            
        Yields:
            Response tokens as they arrive
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Create messages array with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        print(f"\n💬 USER: {user_message}")
        print("🤖 ASSISTANT: ", end="", flush=True)
        
        # Make streaming API call
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            stream=True
        )
        
        # Collect the response
        full_response = ""
        tool_calls_buffer = []
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle text content
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content
            
            # Handle tool calls
            if delta.tool_calls:
                tool_calls_buffer.extend(delta.tool_calls)
        
        print()  # New line after streaming
        
        # If there were tool calls, process them
        if tool_calls_buffer:
            print("\n[Processing tool calls...]")
            # For simplicity in streaming, we'll use the non-streaming approach for tool execution
            # In a production app, you'd want to stream this too
            return self.chat(user_message, stream=False)
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })
        
        return full_response
    
    def reset_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        print("🔄 Conversation history cleared")


def test_agent():
    """Test the pharmacy agent with various scenarios"""
    print("="*80)
    print("🏥 PHARMACY AI AGENT - TEST SCENARIOS")
    print("="*80)
    
    agent = PharmacyAgent()
    
    # Test 1: Simple medication info
    print("\n" + "="*80)
    print("TEST 1: Get Medication Info")
    print("="*80)
    agent.chat("What is Aspirin used for?")
    
    # Test 2: Check inventory
    print("\n" + "="*80)
    print("TEST 2: Check Inventory")
    print("="*80)
    agent.chat("Do you have Semaglutide in stock?")
    
    # Test 3: Check interactions
    print("\n" + "="*80)
    print("TEST 3: Check Drug Interactions")
    print("="*80)
    agent.chat("What does Warfarin interact with?")
    
    # Test 4: Medical advice (should refer to professional)
    print("\n" + "="*80)
    print("TEST 4: Medical Advice Request (Should Refer)")
    print("="*80)
    agent.chat("Should I take Aspirin for my headache?")
    
    # Test 5: Hebrew language
    print("\n" + "="*80)
    print("TEST 5: Hebrew Language Support")
    print("="*80)
    agent.reset_conversation()
    agent.chat("מה זה מטפורמין?")  # "What is Metformin?"
    
    # Test 6: Multi-turn conversation
    print("\n" + "="*80)
    print("TEST 6: Multi-Turn Conversation")
    print("="*80)
    agent.reset_conversation()
    agent.chat("I'm looking for information about Ibuprofen")
    agent.chat("Does it interact with other pain medications?")
    agent.chat("Do you have it in stock?")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED!")
    print("="*80)


def interactive_mode():
    """Run the agent in interactive mode for testing"""
    print("="*80)
    print("🏥 PHARMACY AI AGENT - INTERACTIVE MODE")
    print("="*80)
    print("Type your questions (or 'quit' to exit, 'reset' to clear history)")
    print("="*80)
    
    agent = PharmacyAgent()
    
    while True:
        try:
            user_input = input("\n💬 YOU: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                continue
            
            # Get response (with streaming)
            agent.chat_stream(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Run in interactive mode
        interactive_mode()
    else:
        # Run automated tests
        test_agent()
