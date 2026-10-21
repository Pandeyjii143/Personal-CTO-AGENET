from langgraph.graph import StateGraph, END

from app.graphs.states.repair_state import RepairState
from app.graphs.nodes.validate_node import validate_node
from app.graphs.nodes.repair_node import repair_node
from app.graphs.nodes.test_node import test_node

from app.graphs.routers.validation_router import validation_router
from app.graphs.routers.testing_router import testing_router

builder = StateGraph(RepairState)

builder.add_node("validate", validate_node)
builder.add_node("repair", repair_node)
builder.add_node("test", test_node)

builder.set_entry_point("validate")

builder.add_conditional_edges(
    "validate",
    validation_router,
    {
        "repair": "repair",
        "test": "test",
        "failed": END
    }
)

builder.add_conditional_edges(
    "test",
    testing_router,
    {
        "complete": END,
        "repair": "repair",
        "failed": END
    }
)

builder.add_edge(
    "repair",
    "validate"
)

repair_graph = builder.compile()