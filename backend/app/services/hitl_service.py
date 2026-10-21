from app.agents.hitl_agent import HITLAgent

class HITLService:

    @staticmethod
    def evaluate(task: str):
        return HITLAgent.execute(task)

    @staticmethod
    def collect_project_preferences(requirements):
        return {
            "frontend": "nextjs",
            "backend": "fastapi",
            "database": "postgresql",
            "deployment": "docker"
        }