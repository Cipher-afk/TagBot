task_text = "Task Progress（0/0）"
task_value = task_text.split(" ")[1].lstrip("Progress ").split("/")[1][0]
print(task_value)
