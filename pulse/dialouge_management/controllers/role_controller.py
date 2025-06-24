import re

DEFAULT = """
You are an expert in assistant who assist the user only from the knowledge available to you.

knowledge:''{knowledge}''
User Question: ''{user_question}''
Answer:
"""


class AIRoleController:
    def __init__(self):
        pass

    def get_role_prompt(self, **kwargs) -> str:
        return DEFAULT.format(**kwargs)
    
    def get_placeholders(self) -> list[str]:
        """
        Gets the placeholder keys.
        """
        return re.findall(r'\{([^}]+)\}', DEFAULT)