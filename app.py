"""
Flask Web Application for Pharmacy AI Agent
Provides web UI for chatting with the agent and viewing tool calls
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agent.pharmacy_agent import PharmacyAgent

app = Flask(__name__)
CORS(app)

# Initialize the agent
agent = PharmacyAgent()

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the user"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get response from agent
        response = agent.chat(user_message, stream=False)
        
        # Extract tool calls from conversation history
        tool_calls = []
        if agent.conversation_history:
            last_assistant_msg = None
            for msg in reversed(agent.conversation_history):
                if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                    last_assistant_msg = msg
                    break
            
            if last_assistant_msg and last_assistant_msg.get('tool_calls'):
                for tc in last_assistant_msg['tool_calls']:
                    tool_calls.append({
                        'name': tc['function']['name'],
                        'arguments': json.loads(tc['function']['arguments'])
                    })
        
        return jsonify({
            'response': response,
            'tool_calls': tool_calls
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation"""
    agent.reset_conversation()
    return jsonify({'status': 'success'})

@app.route('/api/stream', methods=['POST'])
def stream():
    """Stream chat responses"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    def generate():
        """Generator for streaming response"""
        try:
            # Add user message to history
            agent.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Create messages
            messages = [
                {"role": "system", "content": agent.system_prompt}
            ] + agent.conversation_history
            
            # Stream response
            stream = agent.client.chat.completions.create(
                model=agent.model,
                messages=messages,
                tools=agent.tools.__class__.__dict__.get('TOOL_DEFINITIONS', []),
                tool_choice="auto",
                stream=True
            )
            
            full_response = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
            
            # Add to history
            agent.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("="*80)
    print("🏥 PHARMACY AI AGENT - WEB INTERFACE")
    print("="*80)
    print("Starting server...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*80)
    app.run(debug=True, port=5000)
