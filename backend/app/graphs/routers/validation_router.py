MAX_REPAIR_ATTEMPTS = 3

def validation_router(state):

    if not state["success"]:

        if state["repair_attempts"] >= MAX_REPAIR_ATTEMPTS:
            return "failed"

        return "repair"

    return "test"