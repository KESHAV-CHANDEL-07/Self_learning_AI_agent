import random
from utils.config import LEARNING_RATE, DISCOUNT_FACTOR, EXPLORATION_RATE, EXPLORATION_DECAY, MIN_EXPLORATION_RATE
from utils.logger import get_logger
from agent.sqlite_dao import SQLiteDAO

logger = get_logger("Decision")

class QLearningDecision:
    def __init__(self, actions_list):
        self.actions_list = actions_list
        self.exploration_rate = EXPLORATION_RATE
        self.learning_rate = LEARNING_RATE
        self.discount_factor = DISCOUNT_FACTOR
        self.dao = SQLiteDAO()

    def get_state_key(self, state):
        """Convert state dictionary to a hashable string key for Q-table."""
        # For simplicity, state is determined by the file extension we are trying to categorize
        return state.get("extension", "unknown").lower()

    def get_action_q(self, state_key, action):
        val = self.dao.get_q(state_key, action)
        return val if val is not None else 0.0

    def choose_action(self, state):
        """Choose action using epsilon-greedy policy."""
        state_key = self.get_state_key(state)
        
        if random.uniform(0, 1) < self.exploration_rate:
            action = random.choice(self.actions_list)
            logger.debug(f"Exploring: chose random action {action} for state {state_key}")
        else:
            # find best action
            best_action = self.actions_list[0]
            best_val = self.get_action_q(state_key, best_action)
            for action in self.actions_list[1:]:
                val = self.get_action_q(state_key, action)
                if val > best_val:
                    best_action = action
                    best_val = val
            action = best_action
            logger.debug(f"Exploiting: chose best action {action} with Q-value {best_val} for state {state_key}")
            
        return action

    def learn(self, state, action, reward, next_state=None):
        """Update Q-value based on the reward received using Q-learning formula."""
        state_key = self.get_state_key(state)
        
        old_value = self.get_action_q(state_key, action)
        # In this simple agent, moving a file completes an episode so next max Q is 0
        next_max = 0 
        
        new_value = (1 - self.learning_rate) * old_value + self.learning_rate * (reward + self.discount_factor * next_max)
        self.dao.set_q(state_key, action, new_value)
        logger.debug(f"Updated Q-value for {state_key}, action {action}: {old_value:.2f} -> {new_value:.2f} (Reward: {reward})")

        # Decay exploration rate
        self.exploration_rate = max(MIN_EXPLORATION_RATE, self.exploration_rate * EXPLORATION_DECAY)

    def save_q_table(self):
        logger.debug("Q-table state is persisted to SQLite DB automatically.")

    def load_q_table(self):
        pass
