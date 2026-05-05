# AI Agent Core

A modular framework for building intelligent agents with tool integration capabilities.

## Features
- Tool registration and execution system
- Core agent logic for task handling
- Easy-to-extend architecture

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/GFJ0814/myAgent.git
   cd myAgent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Import the agent core and tools to build your intelligent agent:
```python
from agent_core import Agent
from tools import ToolRegistry

# Initialize agent
agent = Agent()

# Register tools
registry = ToolRegistry()
agent.register_tools(registry.get_all_tools())

# Run agent
agent.run()
```

## Contributors
- AI Development Team

## License
MIT License
