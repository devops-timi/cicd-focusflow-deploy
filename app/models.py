tasks = []
task_id = 1

def add_task(title):
    global task_id
    task = {
        "id": task_id,
        "title": title,
        "completed": False
    }
    tasks.append(task)
    task_id += 1

def toggle_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]

def get_tasks():
    return tasks
