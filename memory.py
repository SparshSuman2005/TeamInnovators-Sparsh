from collections import deque


class ConversationMemory:

    def __init__(self, max_history=5):

        self.history = deque(maxlen=max_history)

    def add_message(self, role, message):

        self.history.append(
            {
                "role": role,
                "message": message
            }
        )

    def get_history(self):

        history = ""

        for item in self.history:

            history += (
                f"{item['role']}: "
                f"{item['message']}\n"
            )

        return history.strip()

    def clear(self):

        self.history.clear()