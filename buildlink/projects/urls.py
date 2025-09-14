# projects/urls.py
from django.urls import path
from .views import JobListCreateView, JobRetrieveUpdateDestroyView

app_name = 'projects'

urlpatterns = [
    path('jobs/', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:id>/', JobRetrieveUpdateDestroyView.as_view(), name='job-detail'),
]
