import pytest
from agent.decision import QLearningDecision
from utils.config import SUPPORTED_FILE_TYPES

@pytest.fixture
def decision_agent():
    # Pass dummy actions list
    actions = list(SUPPORTED_FILE_TYPES.keys()) + ["misc"]
    return QLearningDecision(actions_list=actions)

def test_get_state_key(decision_agent):
    assert decision_agent.get_state_key({"filename": "invoice_2023.pdf", "extension": ".pdf"}) == ".pdf_invoice"
    assert decision_agent.get_state_key({"filename": "financial_report.pdf", "extension": ".pdf"}) == ".pdf_finance"
    assert decision_agent.get_state_key({"filename": "test_app.py", "extension": ".py"}) == ".py_test"
    assert decision_agent.get_state_key({"filename": "config.yaml", "extension": ".yaml"}) == ".yaml_config"
    assert decision_agent.get_state_key({"filename": "photo.jpg", "extension": ".jpg"}) == ".jpg"
    assert decision_agent.get_state_key({"filename": "main.py", "extension": ".py"}) == ".py_main"

def test_get_heuristic_action(decision_agent):
    assert decision_agent._get_heuristic_action(".pdf_finance") == "documents"
    assert decision_agent._get_heuristic_action(".pdf_invoice") == "documents"
    assert decision_agent._get_heuristic_action(".py_test") == "code"
    
    # Check if yaml is supported, else it defaults to misc (depends on config, assuming it's not in default code exts)
    # The heuristic looks for the base extension
    yaml_action = decision_agent._get_heuristic_action(".yaml_config")
    if ".yaml" in sum(SUPPORTED_FILE_TYPES.values(), []):
        assert yaml_action != "misc"
    else:
        assert yaml_action == "misc"
        
    assert decision_agent._get_heuristic_action(".jpg") == "images"
    assert decision_agent._get_heuristic_action(".exe_unknown") == "misc"
