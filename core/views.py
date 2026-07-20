from core.serializers import TaskSerializer
from core.models import Task
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User, Workspace, Project, Feature
from .serializers import UserSerializer, WorkspaceSerializer, ProjectSerializer, FeatureSerializer

class RegisterAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


class RetrieveUserProfileAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user




class WorkspaceAPIView(generics.ListCreateAPIView):
    queryset = Workspace.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        user = self.request.user
        return Workspace.objects.filter(user=user).prefetch_related(
            'project_set__feature_set__task_set'
        )

class WorkspaceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.prefetch_related(
        'project_set__feature_set__task_set'
    )
    permission_classes = [IsAuthenticated]
    serializer_class = WorkspaceSerializer


class ProjectListCreateAPIView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(workspace__user=user).prefetch_related(
            'feature_set__task_set'
        )


class ProjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.prefetch_related('feature_set__task_set')
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer


class FeatureListCreateAPIView(generics.ListCreateAPIView):
    queryset = Feature.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FeatureSerializer

    def get_queryset(self):
        user = self.request.user
        return Feature.objects.filter(
            project__workspace__user=user
        ).prefetch_related('task_set')


class FeatureDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Feature.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FeatureSerializer

    def get_queryset(self):
        user = self.request.user
        return Feature.objects.filter(
            project__workspace__user=user
        ).prefetch_related('task_set')


class TaskAPIView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(feature__project__workspace__user=user).all()


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(feature__project__workspace__user=user)
