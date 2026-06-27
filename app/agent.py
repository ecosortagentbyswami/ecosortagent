import logging
import json
import re
from datetime import datetime
from google.adk.workflow import Workflow, node, START
from google.adk.events import RequestInput
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool, MCPToolset
from pydantic import BaseModel, Field
from typing import Literal
from .config import config

logger = logging.getLogger(__name__)

from mcp import StdioServerParameters

mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="python",
        args=["app/mcp_server.py"]
    )
)

class EcoSortState(BaseModel):
    user_input: str = ""
    material: str = ""
    guidelines: str = ""
    final_output: str = ""

# 1. Specialized Sub-Agents
waste_analyzer = LlmAgent(
    name="WasteAnalyzer",
    model=config.model,
    instruction="Analyze the user's waste description or text representation. Identify the exact material type (e.g., PET plastic, compostable cardboard, glass). Return a short material summary.",
    tools=[mcp_toolset]
)

local_guideline = LlmAgent(
    name="LocalGuidelineAgent",
    model=config.model,
    instruction="You are an expert on municipal recycling guidelines. Given a material, provide the best practice for sorting it (recycle, compost, or trash). Provide concise, practical advice.",
    tools=[mcp_toolset]
)

# 2. AgentTools for delegation
analyze_tool = AgentTool(agent=waste_analyzer)

guideline_tool = AgentTool(agent=local_guideline)

# 3. Orchestrator
orchestrator = LlmAgent(
    name="OrchestratorAgent",
    model=config.model,
    instruction="""You are the EcoSort Orchestrator. 
1. Use WasteAnalyzer to identify the material from the user's input.
2. Use LocalGuidelineAgent to get the sorting guidelines for that material.
3. If the user input is completely unclear or missing, output 'NEEDS_INFO'.
Otherwise, synthesize the final answer combining the material and guidelines.""",
    tools=[analyze_tool, guideline_tool]
)

def log_audit(severity: str, reason: str, text: str):
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "reason": reason,
        "snippet": text[:50] + "..." if len(text) > 50 else text
    }
    logger.info(f"AUDIT LOG: {json.dumps(audit_entry)}")

# 4. Workflow Nodes
@node
def security_checkpoint(ctx, node_input=None):
    logger.info("Running Security Checkpoint")
    
    if node_input and isinstance(node_input, str) and not ctx.state.get("user_input"):
        user_text = node_input
    else:
        user_text = ctx.state.get("user_input", "")

    # Prompt Injection Detection
    injection_keywords = ["ignore previous instructions", "system prompt", "override", "bypass"]
    for keyword in injection_keywords:
        if keyword in user_text.lower():
            log_audit("CRITICAL", "Prompt injection detected", user_text)
            ctx.state["final_output"] = "Security Error: Prompt injection attempt detected."
            ctx.route = "security_event"
            return
            
    # PII Scrubbing
    scrubbed_text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED PHONE]', user_text)
    if scrubbed_text != user_text:
        log_audit("WARNING", "PII scrubbed (Phone number)", user_text)
        user_text = scrubbed_text
        
    # Domain-specific rule (Hazardous Waste)
    if "hazardous" in user_text.lower() or "medical" in user_text.lower() or "battery" in user_text.lower():
        log_audit("WARNING", "Hazardous waste detected", user_text)
        ctx.state["final_output"] = "Safety Warning: Hazardous or medical waste (e.g., batteries, syringes) must not go in standard bins. Please contact your local waste management for safe disposal."
        ctx.route = "security_event"
        return
        
    log_audit("INFO", "Security check passed", user_text)
    ctx.state["user_input"] = user_text
    ctx.route = "pass"
    return

@node(rerun_on_resume=True)
async def orchestrator_node(ctx):
    logger.info("Running Orchestrator Node")
    response = await ctx.run_node(orchestrator, node_input=ctx.state.get("user_input", ""))
    
    if "NEEDS_INFO" in response:
        ctx.route = "needs_clarification"
        return
    
    ctx.state["final_output"] = response
    ctx.route = "done"
    return

@node
def ask_human_node(ctx):
    logger.info("Requesting Human Input")
    return RequestInput(message="I need more details about the item you want to sort. Could you provide a clearer description?")

@node
def process_human_node(ctx, node_input=None):
    # Note: the new input goes back through security checkpoint in a real app, 
    # but for simplicity we append and go to orchestrator
    current_input = ctx.state.get("user_input", "")
    ctx.state["user_input"] = current_input + f"\nClarification: {node_input}"
    return "ready_to_orchestrate"

@node
def final_output_node(ctx):
    return ctx.state.get("final_output", "")

# 5. Build Workflow Graph
root_agent = Workflow(
    name="ecosort_agent",
    state_schema=EcoSortState,
    edges=[
        (START, security_checkpoint),
        (security_checkpoint, {
            "pass": orchestrator_node,
            "security_event": final_output_node
        }),
        (orchestrator_node, {
            "needs_clarification": ask_human_node,
            "done": final_output_node
        }),
        (ask_human_node, process_human_node, orchestrator_node)
    ]
)
