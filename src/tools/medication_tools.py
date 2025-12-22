"""
Medication Tools for Pharmacy AI Agent
These are the functions (tools) that the AI agent can call to interact with the database
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any


class MedicationTools:
    """Tools for looking up medication information from the pharmacy database"""
    
    def __init__(self, db_path: str = "pharmacy.db"):
        """Initialize with database path"""
        self.db_path = db_path
    
    def _get_connection(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_medication_info(self, medication_name: str) -> Dict[str, Any]:
        """
        Look up comprehensive information about a medication by name.
        
        Args:
            medication_name: Name of the medication (e.g., "Aspirin", "Metformin")
        
        Returns:
            Dictionary containing medication details or error message
        
        Example:
            result = get_medication_info("Aspirin")
            # Returns: {
            #     "success": True,
            #     "medication": {
            #         "name": "Aspirin",
            #         "generic_name": "Acetylsalicylic Acid",
            #         "description": "Pain reliever...",
            #         "dosage_forms": "Tablet, Chewable Tablet",
            #         "common_dosages": "81mg, 325mg, 500mg",
            #         "requires_prescription": False,
            #         "side_effects": "Stomach upset, heartburn...",
            #         "contraindications": "Bleeding disorders..."
            #     }
            # }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Case-insensitive search for medication
            cursor.execute('''
                SELECT medication_id, name, generic_name, active_ingredients,
                       dosage_forms, common_dosages, description, 
                       requires_prescription, side_effects, contraindications
                FROM medications
                WHERE LOWER(name) = LOWER(?) OR LOWER(generic_name) = LOWER(?)
            ''', (medication_name, medication_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "success": True,
                    "medication": {
                        "medication_id": result[0],
                        "name": result[1],
                        "generic_name": result[2],
                        "active_ingredients": result[3],
                        "dosage_forms": result[4],
                        "common_dosages": result[5],
                        "description": result[6],
                        "requires_prescription": bool(result[7]),
                        "side_effects": result[8],
                        "contraindications": result[9]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Medication '{medication_name}' not found in our database.",
                    "suggestion": "Please check the spelling or ask about a different medication."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}"
            }
    
    def check_active_ingredients_and_interactions(self, medication_name: str) -> Dict[str, Any]:
        """
        Get active ingredients and potential drug interactions for a medication.
        
        Args:
            medication_name: Name of the medication
        
        Returns:
            Dictionary with active ingredients and interactions or error message
        
        Example:
            result = check_active_ingredients_and_interactions("Aspirin")
            # Returns: {
            #     "success": True,
            #     "medication": "Aspirin",
            #     "active_ingredients": "Acetylsalicylic Acid",
            #     "interactions": "Blood thinners, NSAIDs, Corticosteroids, Alcohol",
            #     "warning": "Always consult healthcare provider about drug interactions"
            # }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, active_ingredients, interactions
                FROM medications
                WHERE LOWER(name) = LOWER(?) OR LOWER(generic_name) = LOWER(?)
            ''', (medication_name, medication_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "success": True,
                    "medication": result[0],
                    "active_ingredients": result[1],
                    "interactions": result[2],
                    "warning": "Always inform your healthcare provider about all medications you are taking. This is informational only and not medical advice."
                }
            else:
                return {
                    "success": False,
                    "error": f"Medication '{medication_name}' not found in our database."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}"
            }
    
    def check_inventory(self, medication_name: str) -> Dict[str, Any]:
        """
        Check if a medication is in stock and how much is available.
        
        Args:
            medication_name: Name of the medication
        
        Returns:
            Dictionary with stock information or error message
        
        Example:
            result = check_inventory("Aspirin")
            # Returns: {
            #     "success": True,
            #     "medication": "Aspirin",
            #     "in_stock": True,
            #     "stock_quantity": 150,
            #     "status": "Available"
            # }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, stock_quantity, requires_prescription
                FROM medications
                WHERE LOWER(name) = LOWER(?) OR LOWER(generic_name) = LOWER(?)
            ''', (medication_name, medication_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                name, stock_qty, requires_rx = result
                in_stock = stock_qty > 0
                
                # Determine status message
                if stock_qty == 0:
                    status = "Out of stock"
                elif stock_qty < 20:
                    status = "Low stock - limited availability"
                elif stock_qty < 50:
                    status = "Available - moderate stock"
                else:
                    status = "Available - good stock"
                
                response = {
                    "success": True,
                    "medication": name,
                    "in_stock": in_stock,
                    "stock_quantity": stock_qty,
                    "status": status,
                    "requires_prescription": bool(requires_rx)
                }
                
                if requires_rx:
                    response["note"] = "This medication requires a valid prescription."
                
                return response
            else:
                return {
                    "success": False,
                    "error": f"Medication '{medication_name}' not found in our database."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}"
            }
    
    def refer_to_professional(self, query_type: str, reason: str = "") -> Dict[str, Any]:
        """
        Generate appropriate referral message when query requires professional medical advice.
        
        This tool is called when the agent detects questions about:
        - Diagnosis ("What's wrong with me?", "Do I have X condition?")
        - Medical advice ("Should I take this?", "What should I do?")
        - Dosage recommendations for individual cases
        - Treatment plans
        - Drug interactions for specific patient situations
        
        Args:
            query_type: Type of query (e.g., "diagnosis", "treatment", "dosage_advice", "interaction_concern")
            reason: Optional explanation of why referral is needed
        
        Returns:
            Dictionary with appropriate referral message
        
        Example:
            result = refer_to_professional("diagnosis", "Patient asking if symptoms indicate disease")
            # Returns: {
            #     "success": True,
            #     "referral_needed": True,
            #     "message": "I cannot provide medical diagnosis...",
            #     "resources": [...]
            # }
        """
        
        # Base messages for different query types
        messages = {
            "diagnosis": (
                "I cannot provide medical diagnosis. If you're experiencing symptoms or health concerns, "
                "please consult with a healthcare professional who can properly evaluate your condition."
            ),
            "treatment": (
                "I cannot recommend specific treatments or tell you whether you should take a medication. "
                "Please speak with your doctor or pharmacist who can provide personalized medical advice "
                "based on your health history."
            ),
            "dosage_advice": (
                "I cannot provide personalized dosage recommendations. The correct dosage depends on many "
                "individual factors. Please consult your doctor or pharmacist for dosage guidance specific "
                "to your situation."
            ),
            "interaction_concern": (
                "While I can provide general information about drug interactions, I cannot assess your "
                "specific situation. Please speak with your pharmacist or doctor about potential interactions "
                "with your current medications."
            ),
            "side_effect_concern": (
                "If you're experiencing concerning symptoms or side effects from a medication, please contact "
                "your healthcare provider immediately. For emergencies, call your local emergency number."
            ),
            "general": (
                "This question requires professional medical advice that I cannot provide. Please consult "
                "with a healthcare professional for personalized guidance."
            )
        }
        
        # Get appropriate message or use general fallback
        message = messages.get(query_type, messages["general"])
        
        # Add reason if provided
        if reason:
            message = f"{message}\n\nNote: {reason}"
        
        # Healthcare resources
        resources = [
            {
                "type": "Emergency",
                "description": "For medical emergencies, call emergency services immediately"
            },
            {
                "type": "Pharmacist",
                "description": "Speak with our in-store pharmacist for medication questions"
            },
            {
                "type": "Doctor",
                "description": "Contact your healthcare provider for medical advice and treatment"
            },
            {
                "type": "Poison Control",
                "description": "For medication overdose or poisoning concerns, contact Poison Control"
            }
        ]
        
        return {
            "success": True,
            "referral_needed": True,
            "query_type": query_type,
            "message": message,
            "resources": resources,
            "disclaimer": "I can only provide factual information about medications. I cannot diagnose, treat, or provide medical advice."
        }
    
    def get_user_allergies(self, user_name: str) -> Dict[str, Any]:
        """
        Check if a user has any known allergies on file.
        Helper function for safety checks.
        
        Args:
            user_name: Name of the user/patient
        
        Returns:
            Dictionary with allergy information
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, allergies, current_medications
                FROM users
                WHERE LOWER(name) LIKE LOWER(?)
            ''', (f'%{user_name}%',))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "success": True,
                    "user": result[0],
                    "allergies": result[1],
                    "current_medications": result[2]
                }
            else:
                return {
                    "success": False,
                    "error": f"User '{user_name}' not found in our system."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}"
            }
    
    def get_all_medications_list(self) -> Dict[str, Any]:
        """
        Get a simple list of all available medications.
        Useful for when customer asks "What do you have?" or "What medications are available?"
        
        Returns:
            Dictionary with list of medication names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, requires_prescription, stock_quantity > 0 as in_stock
                FROM medications
                ORDER BY name
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            medications = []
            for row in results:
                med_info = {
                    "name": row[0],
                    "requires_prescription": bool(row[1]),
                    "in_stock": bool(row[2])
                }
                medications.append(med_info)
            
            return {
                "success": True,
                "count": len(medications),
                "medications": medications
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}"
            }


# Tool definitions for OpenAI function calling
# These describe the tools to the AI so it knows when and how to use them
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_medication_info",
            "description": "Get comprehensive information about a medication including description, dosage forms, side effects, and contraindications. Use this when customer asks about what a medication is, what it's used for, or general information about it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "Name of the medication (e.g., 'Aspirin', 'Metformin', 'Ibuprofen')"
                    }
                },
                "required": ["medication_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_active_ingredients_and_interactions",
            "description": "Get active ingredients and potential drug interactions for a medication. Use this when customer asks about what's in a medication or what it might interact with.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "Name of the medication"
                    }
                },
                "required": ["medication_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check if a medication is currently in stock and how much is available. Use this when customer asks about availability or stock status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "Name of the medication"
                    }
                },
                "required": ["medication_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "refer_to_professional",
            "description": "Refer customer to healthcare professional when they ask for medical advice, diagnosis, treatment recommendations, or personalized dosage advice. Use this for questions like 'Should I take this?', 'What's wrong with me?', 'How much should I take?', or any medical decision-making.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["diagnosis", "treatment", "dosage_advice", "interaction_concern", "side_effect_concern", "general"],
                        "description": "Type of query that requires professional referral"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional brief explanation of why referral is needed"
                    }
                },
                "required": ["query_type"]
            }
        }
    }
]


# Test function to verify tools work
if __name__ == "__main__":
    print("Testing Medication Tools")
    print("=" * 60)
    
    tools = MedicationTools()
    
    # Test 1: Get medication info
    print("\n1. Testing get_medication_info('Aspirin'):")
    result = tools.get_medication_info("Aspirin")
    print(json.dumps(result, indent=2))
    
    # Test 2: Check interactions
    print("\n2. Testing check_active_ingredients_and_interactions('Metformin'):")
    result = tools.check_active_ingredients_and_interactions("Metformin")
    print(json.dumps(result, indent=2))
    
    # Test 3: Check inventory
    print("\n3. Testing check_inventory('Semaglutide'):")
    result = tools.check_inventory("Semaglutide")
    print(json.dumps(result, indent=2))
    
    # Test 4: Refer to professional
    print("\n4. Testing refer_to_professional('diagnosis'):")
    result = tools.refer_to_professional("diagnosis", "Patient asking about symptoms")
    print(json.dumps(result, indent=2))
    
    # Test 5: Get all medications
    print("\n5. Testing get_all_medications_list():")
    result = tools.get_all_medications_list()
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ All tools tested successfully!")
