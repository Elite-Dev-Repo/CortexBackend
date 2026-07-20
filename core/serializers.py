from rest_framework import serializers
from .models import User, Workspace, Project, Feature, Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user



class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'created_at', 'feature', 'status']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
        }

class FeatureSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True, source='task_set')
    class Meta:
        model = Feature
        fields = ['id', 'name', 'description', 'created_at', 'project', 'tags', 'status', 'tasks']


class ProjectSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True, source='feature_set')
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'workspace', 'features', 'status']


class WorkspaceSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True, source='project_set')
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'created_at', 'user', 'projects']
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, obj):
        user = self.context['request'].user
        if Workspace.objects.filter(user=user).count() >= 3:
            raise serializers.ValidationError("You can only have 3 workspaces")
        workspace = Workspace.objects.create(**obj, user=user)
        return workspace
