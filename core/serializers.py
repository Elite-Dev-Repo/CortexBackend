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
    features = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'workspace', 'features', 'status']


    def get_features(self,obj):
        project = Feature.objects.filter(project=obj)
        return FeatureSerializer(project, many=True).data


class WorkspaceSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'created_at', 'user', 'projects']
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, obj):
        user = self.context['request'].user
        other_workspace = Workspace.objects.filter(user=user)
        if len(other_workspace) >= 3:
            raise serializers.ValidationError("You can only have 3 workspaces")
        workspace = Workspace.objects.create(**obj, user=user)
        return workspace

    def get_projects(self, obj):
        projects = Project.objects.filter(workspace=obj)
        return ProjectSerializer(projects, many=True).data
