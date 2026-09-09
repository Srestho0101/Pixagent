import os
import json
from typing import List, Dict, Any
from mistralai import Mistral
from backend.database import db
from dotenv import load_dotenv

load_dotenv()

class RepairAgent:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        if not self.api_key:
            raise ValueError("Mistral API key not found")
        self.client = Mistral(api_key=self.api_key)
        
    def get_ticket_status(self, ticket_id: int) -> Dict[str, Any]:
        """Fetch current ticket status from database"""
        try:
            result = db.get_client().table("tickets").select("*").eq("id", ticket_id).execute()
            if result.data and len(result.data) > 0:
                ticket = result.data[0]
                return {
                    "success": True,
                    "status": ticket.get("status", "unknown"),
                    "device_info": ticket.get("device_info", "Not specified"),
                    "customer_name": ticket.get("customer_name", "Unknown"),
                    "created_at": ticket.get("created_at", "")
                }
            return {"success": False, "error": "Ticket not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_recent_logs(self, ticket_id: int, limit: int = 5) -> Dict[str, Any]:
        """Fetch recent repair logs for a ticket"""
        try:
            result = db.get_client().table("repair_logs").select("*").eq("ticket_id", ticket_id).order("created_at", desc=True).limit(limit).execute()
            if result.data:
                logs = []
                for log in result.data:
                    logs.append({
                        "id": log.get("id"),
                        "note": log.get("note"),
                        "created_at": log.get("created_at"),
                        "technician_id": log.get("technician_id")
                    })
                return {"success": True, "logs": logs}
            return {"success": True, "logs": []}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_logs(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Fetch all repair logs for a ticket"""
        try:
            result = db.get_client().table("repair_logs").select("*").eq("ticket_id", ticket_id).order("created_at", desc=True).execute()
            if result.data:
                return result.data
            return []
        except Exception as e:
            print(f"Error fetching all logs: {e}")
            return []
    
    def build_system_prompt(self, ticket_id: int) -> str:
        """Build system prompt with ticket context"""
        status_info = self.get_ticket_status(ticket_id)
        
        if not status_info["success"]:
            return f"""You're a repair shop assistant. 
The ticket ID {ticket_id} was not found in our system.
Please politely inform the customer that you cannot find their ticket and suggest they verify the ticket ID or contact the shop directly.
Keep replies to 2-3 sentences."""
        
        logs = self.get_all_logs(ticket_id)
        logs_text = ""
        if logs:
            logs_text = "\n".join([f"- [{log.get('created_at', 'Unknown date')}] {log.get('note', '')}" for log in logs[:5]])
        else:
            logs_text = "No technician logs yet."
        
        return f"""You're a repair shop assistant. 
Ticket status: {status_info['status']}, 
Device: {status_info['device_info']}, 
Customer: {status_info['customer_name']}

Recent logs:
{logs_text}

Rules:
- Greetings → reply warmly
- Progress questions → use logs
- Never guess → only use logs
- If unknown → say "I don't have that info yet"
- Keep replies to 2-3 sentences
- Be helpful but concise"""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Define available tools for Mistral"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_recent_logs",
                    "description": "Get the most recent repair logs for a ticket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "integer",
                                "description": "The ticket ID to fetch logs for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of logs to fetch (default 5)",
                                "default": 5
                            }
                        },
                        "required": ["ticket_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_ticket_status",
                    "description": "Get the current status of a repair ticket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "integer",
                                "description": "The ticket ID to check status for"
                            }
                        },
                        "required": ["ticket_id"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function"""
        if tool_name == "get_recent_logs":
            return self.get_recent_logs(tool_args.get("ticket_id"), tool_args.get("limit", 5))
        elif tool_name == "get_ticket_status":
            return self.get_ticket_status(tool_args.get("ticket_id"))
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def chat(self, ticket_id: int, message: str, history: List[Dict] = None) -> str:
        """Process chat message with tool calling"""
        try:
            messages = []
            
            # Add system prompt
            system_prompt = self.build_system_prompt(ticket_id)
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history
            if history:
                messages.extend(history[-10:])  # Last 10 messages for context
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get tools
            tools = self.get_tools()
            
            # First call: Let Mistral decide if tools are needed
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
            
            # Check if tool calling is needed
            if assistant_message.tool_calls:
                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })
                
                # Execute tools
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    result = self.execute_tool(tool_name, tool_args)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result)
                    })
                
                # Final call with tool results
                final_response = self.client.chat(
                    model=self.model,
                    messages=messages
                )
                
                return final_response.choices[0].message.content
            else:
                # No tools needed, return direct response
                return assistant_message.content
                
        except Exception as e:
            print(f"Error in agent chat: {e}")
            return "I'm sorry, but I'm having trouble accessing the repair information right now. Please try again later or contact the shop directly."

# Singleton instance
agent = RepairAgent()