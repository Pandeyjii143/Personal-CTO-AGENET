class ExecutionContext:

    def __init__(
        self,
        task: str,
        architecture=None,
        milestones=None,
        tasks=None,
        backend_plan=None,
        generated_files=None
    ):

        self.task = task
        self.architecture = architecture
        self.milestones = milestones
        self.tasks = tasks

        self.backend_plan = backend_plan
        self.generated_files = (
            generated_files or {}
        )