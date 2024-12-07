import autogen
from autogen.coding import LocalCommandLineCodeExecutor
import dotenv
import tempfile
from pathlib import Path


dotenv.load_dotenv()

config_list = autogen.config_list_from_json(
   "config.json"
)
temp_dir = tempfile.TemporaryDirectory()

# Get the path to the temporary directory
temp_path = Path(temp_dir.name)

# Create a subdirectory within the temporary directory
sub_dir = temp_path / "subdirectory"
sub_dir.mkdir(exist_ok=True)

executor = LocalCommandLineCodeExecutor(
    timeout=10,
    work_dir=sub_dir,
)

code_executor_agent = autogen.ConversableAgent(
    "code_executor_agent",
    system_message="You are a code executor agent, you'll be given a set of code to execute from the Code Reviewer, download all the neccessary libraries",
    llm_config=False,  # Turn off LLM for this agent.
    code_execution_config={"executor": executor},  # Use the local command line code executor.
    human_input_mode="NEVER",  # Always take human input for this agent for safety.
)


user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message="Take the prompt and if the code is executable pass it on to the Engineer for further processing",
    code_execution_config={
        "work_dir": "code",
        "use_docker": False
    },
    human_input_mode="TERMINATE",
)
engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config = {"config_list" : config_list},
    system_message="""Engineer. You follow an approved plan. Make sure you save code to disk.  You write python/shell 
    code to solve tasks. Wrap the code in a code block that specifies the script type and the name of the file to 
    save to disk.""",
)

code_editor = autogen.AssistantAgent(
    name="Code Reviewer",
    system_message="Code Reviewer. Double check the code make sure it does not have any errors before execution, if the code needs additional libraries be sure to "
                   "address it to the Engineer",
    llm_config = {"config_list" : config_list},

)

group_chat = autogen.GroupChat(
    agents=[user_proxy, engineer, code_editor , code_executor_agent], messages=[], max_round=4, 
)

manager = autogen.GroupChatManager(groupchat=group_chat, llm_config = {"config_list" : config_list},
)

user_proxy.initiate_chat(
    manager,
    message="""
        write a code that shows the pascals triangle upto the 10 iteration
        """,
)