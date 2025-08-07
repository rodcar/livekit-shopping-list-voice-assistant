import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Annotated
from enum import Enum
import os

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, cartesia, silero
from livekit import api
from pydantic import Field

from utils import send_email_via_acs

# Load environment and configure logger
load_dotenv()
logger = logging.getLogger("shopping-voice-assistant")
logger.setLevel(logging.INFO)

STT_MODEL = os.getenv("STT_MODEL")
STT_LANGUAGE = os.getenv("STT_LANGUAGE")
LLM_MODEL = os.getenv("LLM_MODEL")
TTS_MODEL = os.getenv("TTS_MODEL")
TTS_VOICE = os.getenv("TTS_VOICE")
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


class ConfirmationChoice(str, Enum):
    YES = "yes"
    NO = "no"


@dataclass
class ShoppingData:
    """Stores shopping list and state."""
    shopping_list: Dict[str, int] = field(default_factory=dict)
    current_stage: str = "collect_products"
    interactions: List[str] = field(default_factory=list)

    def add_product(self, product: str):
        if product not in self.shopping_list:
            self.shopping_list[product] = 1
            self.interactions.append(f"Added '{product}' to shopping list")


class BaseAgent(Agent):
    """Base agent with common setup and transition logic."""
    
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(
            instructions=instructions,
            stt=deepgram.STT(model=STT_MODEL, language=STT_LANGUAGE),
            llm=openai.LLM(model=LLM_MODEL),
            tts=cartesia.TTS(model=TTS_MODEL, voice=TTS_VOICE, language=TTS_LANGUAGE),
            vad=silero.VAD.load()
        )

    async def transition(self) -> Optional[Agent]:
        """Move to the next agent based on the flow definition."""
        current = self.session.state.get("current_node")
        next_fn = flow.get(current, {}).get("next")
        if not next_fn:
            return None
        
        next_node = next_fn(self.session.state)
        if next_node is None:
            return None
            
        self.session.state["current_node"] = next_node
        agent_cls: Type[Agent] = flow[next_node]["agent"]
        return agent_cls(self.job_context)


class ShoppingListAgent(BaseAgent):
    """Agent for collecting products and detecting when user is done."""
    
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="""You are a helpful shopping voice assistant. Your job is to:

1. Listen to the user when they tell you product names to add to their shopping list
2. Add each product they mention to the shopping list using the 'add_product' function
3. When the user indicates they are finished (e.g., says "I'm done", "that's all", "finish", "complete my list"), call the 'finish_shopping' function

Be friendly and confirm each product as you add it. Ask clarifying questions if needed.
Examples of what users might say:
- "Add milk to my list"
- "I need bread and eggs"  
- "Put down some apples"
- "I'm done" or "That's all" (when they want to finish)
"""
        )

    async def on_enter(self) -> None:
        await self.session.say("Hi! I'm your shopping assistant. Tell me what products you'd like to add to your shopping list. When you're done, just say 'I'm finished' or 'that's all'.")

    @function_tool
    async def add_product(self, product_name: str) -> str:
        """Add a product to the shopping list.
        
        Args:
            product_name: The name of the product to add to the shopping list
        """
        shopping_data: ShoppingData = self.session.userdata
        
        if product_name in shopping_data.shopping_list:
            logger.info(f"Product already exists (not adding duplicate): {product_name}")
        else:
            shopping_data.add_product(product_name)
            logger.info(f"Added product: {product_name}")
        
        return f"Got it! What else would you like to add?"

    @function_tool
    async def finish_shopping(self) -> Optional[Agent]:
        """Call this when the user indicates they are done adding products to their shopping list."""
        logger.info("User finished adding products, transitioning to summary")
        return await self.transition()


class SummaryAgent(BaseAgent):
    """Agent that summarizes the shopping list and asks about sending it via email."""
    
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="You will present the final shopping list to the user and ask if they want to send it via email."
        )

    async def on_enter(self) -> None:
        shopping_data: ShoppingData = self.session.userdata
        
        if not shopping_data.shopping_list:
            summary = "Your shopping list is empty. Have a great day!"
            await self.session.say(summary)
            return
        else:
            products = "\n".join([f"- {product}" for product in shopping_data.shopping_list.keys()])
            summary = f"Here's your complete shopping list:\n\n{products}\n\nWould you like me to send this shopping list to your email?"
        
        await self.session.say(summary)
        logger.info("Shopping list summary presented")
        
        # Print shopping list to console
        print("\n=== SHOPPING LIST COMPLETE ===")
        for i, product in enumerate(shopping_data.shopping_list.keys(), 1):
            print(f"{i}. {product}")
        print("==============================\n")

    @function_tool
    async def confirm_email_send(
        self, 
        choice: Annotated[
            ConfirmationChoice, 
            Field(description="Does the user want to send the shopping list via email? Answer 'yes' or 'no'")
        ]
    ) -> Optional[Agent]:
        """Handle user's confirmation about sending email."""
        logger.info(f"User choice for email send: {choice.value}")
        
        if choice == ConfirmationChoice.YES:
            return await self.transition()
        else:
            await self.session.say("No problem! Your shopping list is complete. Have a great day!")
            logger.info("User declined email send. Ending session.")
            return None


class EmailDeliveryAgent(BaseAgent):
    """Agent that sends the shopping list via email."""
    
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="You will send the shopping list via email and confirm completion."
        )

    async def on_enter(self) -> None:
        shopping_data: ShoppingData = self.session.userdata
        
        await self.session.say("Perfect! I'm sending your shopping list to your email now...")
        
        # Send the email
        success = await self.send_shopping_list_email(shopping_data)
        
        if success:
            await self.session.say("Great! Your shopping list has been successfully sent to your email. You can check your inbox now. Have a wonderful shopping trip!")
            logger.info("Shopping list sent via email successfully. Session ending.")
        else:
            await self.session.say("I'm sorry, there was an issue sending your email. Please check your email configuration or try again later.")
            logger.error("Failed to send shopping list email. Session ending.")

    async def send_shopping_list_email(self, shopping_data: ShoppingData) -> bool:
        """Send the shopping list via email using Azure Communication Services."""
        import asyncio
        
        logger.info("🔄 Starting email send process...")
        
        # Check if recipient email is configured
        if not RECIPIENT_EMAIL:
            logger.error("RECIPIENT_EMAIL not configured")
            return False
        
        # Create simple text content
        items_text = "\n".join([f"• {product}" for product in shopping_data.shopping_list.keys()])
        
        subject = "Your Shopping List"
        plain_text = f"Here's your shopping list:\n\n{items_text}\n\nHappy shopping!"
        html_content = ""
        
        try:
            # Send email using the utility function
            success = send_email_via_acs(
                to_email=RECIPIENT_EMAIL,
                subject=subject,
                plain_text=plain_text,
                html_content=html_content
            )
            
            if success:
                logger.info(f"Shopping list sent to {RECIPIENT_EMAIL}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Items sent: {list(shopping_data.shopping_list.keys())}")
                
                # Print confirmation to console
                print("\n=== EMAIL SENT ===")
                print(f"Successfully sent to {RECIPIENT_EMAIL}")
                print(f"Subject: {subject}")
                print(f"Items: {', '.join(shopping_data.shopping_list.keys())}")
                print("==================\n")
                
                return True
            else:
                logger.error("Failed to send email via ACS")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False


# Flow definition
flow = {
    "collect_products": {
        "agent": ShoppingListAgent,
        "next": lambda state: "summary"
    },
    "summary": {
        "agent": SummaryAgent,
        "next": lambda state: "email_send"
    },
    "email_send": {
        "agent": EmailDeliveryAgent,
        "next": None
    }
}


async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    session.userdata = ShoppingData()
    session.state = {"current_node": "collect_products"}
    
    await session.start(agent=ShoppingListAgent(ctx), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))