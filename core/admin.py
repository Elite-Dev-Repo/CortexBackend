from django.contrib import admin
from .models import User, Workspace, Project, Feature, Task

# Register your models here.
admin.site.register(User)
admin.site.register(Workspace)
admin.site.register(Project)
admin.site.register(Feature)
admin.site.register(Task)
