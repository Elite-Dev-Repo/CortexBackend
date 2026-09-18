from rest_framework import serializers
from .models import User, Workspace, Project, Feature, Task, OTP, TeamMember, Edge


def _validate_position(value):
    if value is None:
        return {"x": 0, "y": 0}
    if not isinstance(value, dict):
        raise serializers.ValidationError("position must be an object {x: number, y: number}")
    try:
        x = int(round(float(value.get("x", 0))))
        y = int(round(float(value.get("y", 0))))
    except Exception:
        raise serializers.ValidationError("position.x and position.y must be numbers")
    # clamp to PositiveSmallInteger-like range (0..32767)
    x = max(0, min(32767, x))
    y = max(0, min(32767, y))
    return {"x": x, "y": y}

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'user', 'otp', 'expires_at']
        read_only_fields = ['user', 'otp', 'expires_at']


class TaskSerializer(serializers.ModelSerializer):
    position = serializers.JSONField(required=False)

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'created_at', 'feature', 'status', 'position']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
        }

    def validate_position(self, value):
        return _validate_position(value)


class FeatureSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True, source='task_set')
    position = serializers.JSONField(required=False)

    class Meta:
        model = Feature
        fields = ['id', 'name', 'description', 'created_at', 'project', 'tags', 'status', 'tasks', 'position']

    def validate_position(self, value):
        return _validate_position(value)


class ProjectSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True, source='feature_set')
    position = serializers.JSONField(required=False)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'workspace', 'features', 'status', 'position']

    def validate_position(self, value):
        return _validate_position(value)


class WorkspaceSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True, source='project_set')
    class Meta:
        model = Workspace
        fields = ['id', 'user', 'name', 'description', 'workspace_type',  'created_at', 'projects']
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, obj):
        user = self.context['request'].user
        if Workspace.objects.filter(user=user).count() >= 3:
            raise serializers.ValidationError("You can only have 3 workspaces")
        workspace = Workspace.objects.create(**obj, user=user)
        return workspace


class DashboardSidebarSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True, many=True)
    class Meta:
        model = User
        fields = ["email", "workspace"]


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = "__all__"


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ['id','animated', 'source', 'target', 'targetHandle', 'user' ]
        extra_kwargs = {'user': {'read_only': True}}


        def create(self, validated_data):
            user = self.context['request'].user
            data_id = validated_data['id']

            if Edge.objects.filter(id=data_id).exists():
                raise serializers.ValidationError('Edge already exists')
            validated_data['user'] = user
            return super().create(validated_data)