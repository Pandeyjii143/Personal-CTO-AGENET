MAX_REPAIR_ATTEMPTS = 3


def testing_router(state):

    if state["test_success"]:
        return "complete"

    if (
        state["repair_attempts"]
        >= MAX_REPAIR_ATTEMPTS
    ):
        return "failed"

    return "repair"