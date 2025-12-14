def log_state(label: str, state):
    """Log the current state before a node executes."""
    print("\n--------------------------------------------")
    print(f"STATE BEFORE: [{label}]")
    print("--------------------------------------------")
    for k, v in state.dict().items():
        print(f"{k}: {repr(v)[:180]}")  
    print("--------------------------------------------\n")


def log_update(label: str, updates: dict):
    """Log the updates returned by a node."""
    print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"STATE UPDATE FROM NODE: [{label}]")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    for k, v in updates.items():
        print(f"{k}: {repr(v)[:180]}")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")