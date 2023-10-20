from django.http import HttpResponseRedirect
from django.views.generic import CreateView, ListView

from .models import Task
from .services import task_create, NoWorkers


class TaskListView(ListView):
    template_name = "tasks/list.html"
    model = Task

    def get_queryset(self):
        return [
            {
                "title": "Hello World",
                "description": "Write a 'Hello World' Python script.",
                "jira_id": "BE-1337",
                "assignee": "workerworkerworkerworkerworkerworker@example.com",
                "status": "assigned",
            },
            {
                "title": "Hello World",
                "description": "Write a 'Hello World' Python script.",
                "jira_id": "BE-1337",
                "assignee": "worker@example.com",
                "status": "completed",
            },
            {
                "title": "Hello World",
                "description": "Write a 'Hello World' Python script.",
                "jira_id": "BE-1337",
                "assignee": "worker@example.com",
                "status": "assigned",
            },
            {
                "title": "Hello World",
                "description": "Write a 'Hello World' Python script.",
                "jira_id": "BE-1337",
                "assignee": "worker@example.com",
                "status": "completed",
            },
        ]



class TaskCreateView(CreateView):
    template_name = "tasks/create.html"

    model = Task
    fields = ["title", "description"]

    success_url = "tasks:list"

    def form_valid(self, form):
        try:
            self.object = task_create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
            )
        except NoWorkers:
            form.add_error(None, "Task cannot be created - no Workers available.")
            return super().form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class ReshuffleView(object):
    ...
