"""AI Engine - Multi-agent conversation system."""
import os
import time
import json
import httpx
import asyncio
from typing import Optional
from collections import defaultdict

from app.core.config import settings


class AIEngine:
    """Multi-agent AI engine for customer support."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.agents = {}
        self.conversation_history = defaultdict(list)
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI agents."""
        self.agents = {
            "general": Agent(
                name="General Support",
                system_prompt="""You are the Verdis AI Customer Success agent. You provide accurate, helpful support for the Verdis blockchain ecosystem (VerdisChain, EvolvixOS, wallets, validators, developers).

Rules:
- Always be professional and concise
- Cite documentation when possible
- If you don't know something, say so and offer to create a ticket
- Never invent information
- Support multiple languages
- Use markdown formatting for code blocks
- Escalate to human when: legal, financial, security, identity verification, refunds, critical infrastructure""",
                model=self.model,
                api_key=self.api_key,
            ),
            "technical": Agent(
                name="Technical Support",
                system_prompt="""You are the Verdis Technical Support agent specializing in:
- Blockchain node operations (Substrate, DPoS consensus)
- RPC API debugging
- Smart contract development
- SDK integration
- Wallet integration
- Explorer (Verdiscan) issues

Provide step-by-step technical guidance with code examples when needed. Use markdown code blocks. Always verify API endpoints exist before suggesting them.""",
                model=self.model,
                api_key=self.api_key,
            ),
            "blockchain": Agent(
                name="Blockchain Support",
                system_prompt="""You are the Verdis Blockchain Support agent specializing in:
- Node diagnostics and health monitoring
- Consensus (BABE/GRANDPA/DPoS)
- Validator setup and management
- Peer connectivity and sync issues
- Block production and finality
- AMM DEX operations
- Carbon credit and eco tracking

Analyze logs, RPC responses, and metrics. Provide actionable diagnostics.""",
                model=self.model,
                api_key=self.api_key,
            ),
            "merchant": Agent(
                name="Merchant Support",
                system_prompt="""You are the Verdis Merchant Support agent. Help merchants with:
- Onboarding and account setup
- QR code troubleshooting
- Dashboard analytics
- Settlement and payment issues
- Campaign management
- Account verification

Be business-friendly and solution-oriented.""",
                model=self.model,
                api_key=self.api_key,
            ),
            "developer": Agent(
                name="Developer Support",
                system_prompt="""You are the Verdis Developer Support agent. Help developers with:
- SDK usage (TypeScript/JavaScript)
- API authentication and webhooks
- Smart contract deployment (VRC-20, VRC-721)
- Node setup and configuration
- RPC method documentation
- Code examples and debugging

Always provide working code examples. Link to API docs when available.""",
                model=self.model,
                api_key=self.api_key,
            ),
        }
        self._initialized = True
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        agent_type: str = "general",
        context: Optional[dict] = None,
        knowledge_context: Optional[str] = None,
    ) -> dict:
        """Process a chat message through the AI engine."""
        agent = self.agents.get(agent_type, self.agents["general"])
        
        # Build conversation history
        history = self.conversation_history.get(conversation_id or "default", [])
        
        # Build messages
        messages = [{"role": "system", "content": agent.system_prompt}]
        
        # Add knowledge context if available
        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"Knowledge Base Context:\n{knowledge_context}"
            })
        
        # Add user context
        if context:
            messages.append({
                "role": "system",
                "content": f"User Context: {json.dumps(context)}"
            })
        
        # Add conversation history (last 10 messages)
        for msg in history[-10:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self._call_openai(messages)
            
            # Store in history
            if conversation_id:
                self.conversation_history[conversation_id].append(
                    {"role": "user", "content": message}
                )
                self.conversation_history[conversation_id].append(
                    {"role": "assistant", "content": response}
                )
            
            # Detect escalation need
            escalation = self._detect_escalation(message, response)
            
            return {
                "response": response,
                "agent": agent.name,
                "agent_type": agent_type,
                "conversation_id": conversation_id,
                "escalation_needed": escalation,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        except Exception as e:
            import traceback
            print(f"CHAT ERROR: {e}")
            print(traceback.format_exc())
            return {
                "response": f"I encountered an issue processing your request. Let me create a ticket for this. Error: {str(e)[:100]}",
                "agent": agent.name,
                "agent_type": agent_type,
                "conversation_id": conversation_id,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
    
    async def _call_openai(self, messages: list) -> str:
        """Call OpenAI API."""
        if not self.api_key:
            return "AI engine is not configured. Please set OPENAI_API_KEY_2. Meanwhile, I can still help create tickets and search the knowledge base."
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    def _detect_escalation(self, user_msg: str, ai_response: str) -> bool:
        """Detect if human escalation is needed."""
        escalation_keywords = [
            "legal", "lawsuit", "attorney", "lawyer",
            "refund", "chargeback", "reimbursement",
            "identity verification", "kyc", "aml",
            "security breach", "hack", "stolen funds",
            "enterprise contract", "sla", "partnership",
            "human agent", "human support", "real person",
            "manager", "supervisor",
        ]
        msg_lower = (user_msg + " " + ai_response).lower()
        return any(kw in msg_lower for kw in escalation_keywords)
    
    def classify_intent(self, message: str) -> dict:
        """Classify user intent and route to appropriate agent."""
        msg_lower = message.lower()
        
        # Technical keywords
        if any(kw in msg_lower for kw in ["node", "rpc", "api", "sdk", "code", "bug", "error", "crash"]):
            return {"agent_type": "technical", "ticket_type": "technical", "priority": "medium"}
        
        # Blockchain keywords
        if any(kw in msg_lower for kw in ["validator", "block", "consensus", "staking", "slashing", "peer", "sync", "blockchain"]):
            return {"agent_type": "blockchain", "ticket_type": "blockchain", "priority": "medium"}
        
        # Merchant keywords
        if any(kw in msg_lower for kw in ["merchant", "payment", "qr", "settlement", "dashboard", "campaign"]):
            return {"agent_type": "merchant", "ticket_type": "merchant", "priority": "medium"}
        
        # Developer keywords
        if any(kw in msg_lower for kw in ["smart contract", "deploy", "webhook", "token", "vrc", "nft", "dapp"]):
            return {"agent_type": "developer", "ticket_type": "developer", "priority": "medium"}
        
        # Security keywords
        if any(kw in msg_lower for kw in ["hack", "stolen", "breach", "vulnerability", "exploit", "security"]):
            return {"agent_type": "general", "ticket_type": "security", "priority": "critical"}
        
        # Billing keywords
        if any(kw in msg_lower for kw in ["billing", "invoice", "payment", "subscription", "refund"]):
            return {"agent_type": "general", "ticket_type": "billing", "priority": "high"}
        
        return {"agent_type": "general", "ticket_type": "technical", "priority": "low"}
    
    def clear_history(self, conversation_id: str):
        """Clear conversation history."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]


class Agent:
    """Individual AI agent."""
    def __init__(self, name: str, system_prompt: str, model: str, api_key: str):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.api_key = api_key
