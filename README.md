# EcoSort Agent ♻️

An AI-powered municipal waste sorting assistant built on the **Google Agent Development Kit (ADK) 2.0** graph workflow. This project is a submission for the Agentic Capstone Project.

The EcoSort Agent intelligently analyzes waste descriptions, cross-references local municipal guidelines using a local Model Context Protocol (MCP) server, enforces strict security protocols (prompt injection detection and PII scrubbing), and incorporates a Human-in-the-loop (HITL) system when clarification is needed.

## Quick Start

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd ecosort-agent
   ```

2. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
   *Add your `GOOGLE_API_KEY` to the `.env` file.*

3. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

4. Launch the local interactive playground:
   ```bash
   make playground
   ```
   *(Or on Windows, run: `uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents`)*

## Architecture

![Architecture Diagram](assets/architecture_diagram.png)

This agent uses a state-machine graph workflow composed of the following core nodes:
- **Security Checkpoint**: Intercepts prompt injections, scrubs phone numbers (PII), and enforces hazardous waste rules (e.g. medical waste).
- **Orchestrator Agent**: Delegates tasks to specialized sub-agents.
  - **Waste Analyzer Sub-Agent**: Identifies the exact material type.
  - **Local Guideline Sub-Agent**: Connects to the local MCP server to fetch sorting rules for San Francisco, Seattle, etc.
- **Human Pause Node**: A Human-in-the-loop (HITL) step that triggers a `RequestInput` if the user's description is too vague.

## How to Run

- **Interactive UI Testing (Playground)**:
  ```bash
  make playground
  ```
  Access the web interface at `http://localhost:18081`.

- **Local Web Server (FastAPI)**:
  ```bash
  make run
  ```

## Sample Test Cases

Here are three test cases specific to EcoSort to verify its behavior:

### Test Case 1: Standard Recycling Query
- **Input**: `"I have an empty plastic water bottle and I live in San Francisco."`
- **Expected**: Security node passes the text. The Orchestrator delegates to WasteAnalyzer (PET plastic) and LocalGuidelineAgent (San Francisco rules via MCP). Output advises the blue recycling bin.
- **Check**: The playground UI outputs the final formatted text without prompting for more info.

### Test Case 2: Vague Query (Triggers HITL)
- **Input**: `"Where does this weird shiny wrapper go?"`
- **Expected**: Security node passes the text. The Orchestrator is unable to determine the exact material and outputs `NEEDS_INFO`, routing the workflow to the Human Pause node.
- **Check**: The playground UI pauses and prompts: *"I need more details about the item you want to sort. Could you provide a clearer description?"*

### Test Case 3: Hazardous Waste (Security Block)
- **Input**: `"I need to throw away some old medical syringes and batteries."`
- **Expected**: The Security Checkpoint detects hazardous keywords ("medical", "battery"). The workflow immediately routes to the security_event terminal node, bypassing the LLM.
- **Check**: The playground UI outputs the safety warning: *"Safety Warning: Hazardous or medical waste (e.g., batteries, syringes) must not go in standard bins..."*




