from flask import Blueprint, render_template, request, redirect, url_for
from .models import add_task, toggle_task, get_tasks

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        title = request.form.get("title")
        if title:
            add_task(title)
        return redirect(url_for("main.tasks"))

    return render_template("tasks.html", tasks=get_tasks())

@main.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    toggle_task(task_id)
    return ("", 204)
