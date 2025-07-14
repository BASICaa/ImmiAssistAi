from django.shortcuts import render
from django.http import JsonResponse
from .forms import QueryForm, ImmigrationProfileForm
from .tasks import process_user_query_task, process_profile_form_task
from celery.result import AsyncResult
from .Agents.Classes import output_agent
from .Agents.logging_config import AppLogger
import datetime
import json

logger = AppLogger(log_file='views_debug.log').get_logger()

def chat_interface(request):
    logger.info(f"[Timestamp] chat_interface started at: {datetime.datetime.now()}")
    
    if request.method == "POST":
        # Handle JSON submission from the profile form
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                print(f"Received JSON data for profile form: {data}")
                with open('output.json', 'w') as json_file:
                    # Save the data
                    json.dump(data, json_file, indent=4)
                logger.debug(f"Received JSON data for profile form: {data}")
                task = process_profile_form_task.delay("Save Gathered Data")
                return JsonResponse({"task_id": task.id})
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Handle FormData submission from the initial agent query
        if "agentForm" in request.POST:
            form = QueryForm(request.POST)
            if form.is_valid():
                user_query = form.cleaned_data['user_msg']
                task = process_user_query_task.delay(user_query)
                return JsonResponse({"task_id": task.id})

    # For GET requests or other cases, just render the page
    return render(request, "chat_interface.html", {"form": QueryForm()})

def get_task_result(request, task_id):
    """
    Pollable endpoint to check the status and get the result of a Celery task.
    """
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.successful() else None,
    }
    return JsonResponse(result)

def profile_creation_view(request):
    """
    Renders the profile creation form.
    """
    return render(request, 'profile_creation.html', {'form': ImmigrationProfileForm()})