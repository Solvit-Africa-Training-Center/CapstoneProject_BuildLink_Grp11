from django.contrib import admin
from .models import NationalID, User, Job, Application, Trade, WorkerTrade, Portfolio, Rating, GovernmentProject, Notification


admin.site.site_header= "BuildLink Admin Portal"
admin.site.site_title= "BuildLink"

admin.site.register(NationalID)
admin.site.register(User)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(Trade)
admin.site.register(WorkerTrade)
admin.site.register(Portfolio)
admin.site.register(Rating)
admin.site.register(GovernmentProject)
admin.site.register(Notification)


# Register your models here.
