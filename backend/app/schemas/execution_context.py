class ExecutionContext:

    def __init__(
        self,
        task: str,
        architecture=None,
        milestones=None,
        tasks=None
    ):
        self.task = task
        self.architecture = architecture
        self.milestones = milestones
        self.tasks = tasks