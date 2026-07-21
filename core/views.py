from datetime import timedelta
from core.serializers import TaskSerializer
from core.models import Task, OTP, User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User, Workspace, Project, Feature
from .serializers import UserSerializer, WorkspaceSerializer, ProjectSerializer, FeatureSerializer, OTPSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from .services import send_otp_email

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


class VerifyEmailAPiView(APIView):
    def post(self, request):
        code = request.data.get('code')
        otp = OTP.objects.filter(otp=code).first()
        if not otp:
            return Response({'error': 'Invalid Code'}, status=status.HTTP_400_BAD_REQUEST)
        if otp.expires_at < timezone.now():
            return Response({'error': 'Code expired'}, status=status.HTTP_400_BAD_REQUEST)
        otp.user.is_active = True
        otp.user.save()
        otp.delete()
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)


class ResendOTPTokenAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        email_user = User.objects.get(email=email)
        if not email_user:
            return Response({'error': 'Incorrect details'}, status = status.HTTP_400_BAD_REQUEST)
        if email_user.is_active:
            return Response({'error': 'Account Already Verified'}, status = status.HTTP_400_BAD_REQUEST)
        otp = OTP.objects.create(user=email_user, expires_at=timezone.now() + timedelta(minutes=10))
        send_otp_email(email, otp.otp)
        return Response({'message': 'OTP sent successfully'}, status = status.HTTP_200_OK)
        

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



