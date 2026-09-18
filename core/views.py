from datetime import timedelta
from core.serializers import TaskSerializer
from core.models import Task, OTP, User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User, Workspace, Project, Feature, Edge
from .serializers import UserSerializer, WorkspaceSerializer, ProjectSerializer, FeatureSerializer, OTPSerializer, DashboardSidebarSerializer, EdgeSerializer
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

class DashboardSidebarAPIView(generics.RetrieveAPIView):
    queryset = User.objects.prefetch_related("workspace").all()
    permission_classes = [IsAuthenticated]
    serializer_class = DashboardSidebarSerializer

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



class EdgeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Edge.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = EdgeSerializer

    def get_queryset(self):
        user = self.request.user
        return Edge.objects.filter(user=user)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("User must be authenticated to create an edge.")
        
        serializer.save(user=self.request.user)


class BulkPositionSyncAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _normalize_pos(self, pos):
        if not isinstance(pos, dict):
            return None
        try:
            x = int(round(float(pos.get("x", 0))))
            y = int(round(float(pos.get("y", 0))))
        except Exception:
            return None
        x = max(0, min(32767, x))
        y = max(0, min(32767, y))
        return {"x": x, "y": y}

    def post(self, request):
        # Accept either {positions: [...] } or plain list, or {updates: [...]}
        payload = request.data
        if isinstance(payload, dict) and "positions" in payload:
            items = payload["positions"]
        elif isinstance(payload, dict) and "updates" in payload:
            items = payload["updates"]
        elif isinstance(payload, list):
            items = payload
        else:
            # also support legacy {nodes:[...]}?
            items = payload.get("nodes", None) if isinstance(payload, dict) else None
            if items is None:
                return Response({"error": "Expected 'positions' list or array"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(items, list):
            return Response({"error": "'positions' must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        updated = []
        errors = []

        for entry in items:
            if not isinstance(entry, dict):
                errors.append({"entry": entry, "error": "must be object"})
                continue
            raw_id = entry.get("id")
            pos = entry.get("position")
            if raw_id is None or pos is None:
                errors.append({"id": raw_id, "error": "id and position required"})
                continue
            norm = self._normalize_pos(pos)
            if norm is None:
                errors.append({"id": raw_id, "error": "invalid position"})
                continue

            # Try Project (UUID), then Feature, then Task — respecting ownership
            obj = None
            model_name = None
            # hint: entry may include "model" or "type"
            hint = (entry.get("model") or entry.get("type") or "").lower()

            def try_project():
                try:
                    return Project.objects.get(id=raw_id, workspace__user=user)
                except Exception:
                    return None

            def try_feature():
                try:
                    # Feature PK is int
                    fid = int(raw_id) if isinstance(raw_id, str) and raw_id.isdigit() else raw_id
                    return Feature.objects.get(id=fid, project__workspace__user=user)
                except Exception:
                    return None

            def try_task():
                try:
                    tid = int(raw_id) if isinstance(raw_id, str) and raw_id.isdigit() else raw_id
                    return Task.objects.get(id=tid, feature__project__workspace__user=user)
                except Exception:
                    return None

            if hint == "project":
                obj = try_project()
                model_name = "project" if obj else None
            elif hint == "feature":
                obj = try_feature()
                model_name = "feature" if obj else None
            elif hint == "task":
                obj = try_task()
                model_name = "task" if obj else None
            else:
                # auto-detect: project first (UUID), then feature, then task
                obj = try_project()
                if obj:
                    model_name = "project"
                else:
                    obj = try_feature()
                    if obj:
                        model_name = "feature"
                    else:
                        obj = try_task()
                        if obj:
                            model_name = "task"

            if not obj:
                errors.append({"id": raw_id, "error": "not found or not owned"})
                continue

            obj.position = norm
            obj.save(update_fields=["position"])
            updated.append({"id": str(raw_id), "model": model_name, "position": norm})

        return Response({"updated": updated, "errors": errors}, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)