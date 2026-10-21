# test_orchestrator.py

from app.agents.orchestrator import Orchestrator

if __name__ == "__main__":
    task = """
    Build a FastAPI authentication system with JWT login,
    register, users table and PostgreSQL.
    """

    result = Orchestrator.execute(task)

    print("\n=== DONE ===\n")
    print(result)