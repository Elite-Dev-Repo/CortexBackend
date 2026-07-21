from core.views import TaskDetailAPIView
from core.views import TaskAPIView
from django.urls import path
from .views import RegisterAPIView, WorkspaceAPIView, ProjectListCreateAPIView, FeatureListCreateAPIView, RetrieveUserProfileAPIView, WorkspaceDetailAPIView, ProjectDetailAPIView, FeatureDetailAPIView, VerifyEmailAPiView, ResendOTPTokenAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-email/', VerifyEmailAPiView.as_view(), name='verify-email'),
    path('resend-otp/', ResendOTPTokenAPIView.as_view(), name='resend-otp'),
    path('profile/', RetrieveUserProfileAPIView.as_view(), name='profile'),
    path('workspaces/', WorkspaceAPIView.as_view(), name='workspaces'),
    path('workspace/<uuid:pk>/', WorkspaceDetailAPIView.as_view(), name='workspace-detail'),
    path('projects/', ProjectListCreateAPIView.as_view(), name='projects'),
    path('project/<uuid:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('features/', FeatureListCreateAPIView.as_view(), name='features'),
    path('feature/<int:pk>/', FeatureDetailAPIView.as_view(), name='feature-detail'),
    path('tasks/', TaskAPIView.as_view(), name='tasks'),
    path('task/<int:pk>/', TaskDetailAPIView.as_view(), name='task-detail'),
]