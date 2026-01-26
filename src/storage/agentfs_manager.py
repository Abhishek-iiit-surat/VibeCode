from agentfs_sdk import AgentFS
from dataclasses import dataclass

@dataclass
class AgentFSOptions:
    """Options object for AgentFS.open()"""
    id: str
    path: str = None

class AgentFSManager:

    def __init__(self):
        self.agent = None

    async def initialize_agent(self, agent_id: str = "vibe-session"):
        """
        Initialize AgentFS agent using agent id.

        Args:
            agent_id (str): Unique identifier for this VibeCode session (default: "vibe-session")

        Returns:
            self: Returns the manager instance for chaining
        """
        # Create options object for AgentFS.open()
        options = AgentFSOptions(id=agent_id)
        self.agent = await AgentFS.open(options)
        return self

    async def write_to_sandbox(self, file_path: str, content: str):
        """Write content to a file in the AgentFS sandbox"""
        await self.agent.fs.write_file(file_path, content)
        return file_path

    async def read_from_sandbox(self, file_path: str):
        """Read from sandboxed file"""
        return await self.agent.fs.read_file(file_path)

    async def apply_to_real_file(self, file_path: str):                                                
        """Copy from sandbox to real filesystem"""   
        content = await self.read_from_sandbox(file_path)                    
        with open(file_path, 'w') as f:              
            f.write(content)                         
                                                       
    async def close(self):                           
        """Cleanup sandbox"""                        
        if self.agent:                               
            await self.agent.close() 
    
