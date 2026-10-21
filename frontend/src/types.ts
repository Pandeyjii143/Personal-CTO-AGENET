export type Project = {
  id: number
  name: string
  description: string
  goal: string
  status: string
  progress: number
}

export type ProjectInput = Pick<Project, 'name' | 'description' | 'goal'>

export type Blueprint = {
  id: number
  project_id: number
  architecture: Record<string, unknown>
  tech_stack: string[]
  risks: string[]
  status: string
}

export type Milestone = {
  id: number
  project_id: number
  title: string
  description: string
  status: string
  order_index: number
}

export type Task = {
  id: number
  project_id: number
  milestone_id: number
  title: string
  description: string
  status: string
  priority: string
  order_index: number
}
