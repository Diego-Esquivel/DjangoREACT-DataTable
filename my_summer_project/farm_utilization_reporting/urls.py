from django.urls import path, re_path

from . import views

urlpatterns = [
    path('clearAndUpdateListPending/',views.clearAndUpdateListPending),
    path('clearAndUpdateList/',views.clearAndUpdateList),
    path('cronPoint/',views.cronJobView),
    path('listpending/',views.listpending),
    path('listpending/listpendingdata/',views.listpendingdata),
    path('list/',views.list),
    path('list/listdata/',views.listdata),
    path('data/',views.data),
    path('data/datadata/',views.datadata),
    path('data/datadata_dep/',views.datadata_dep),
    re_path('.*/styles/',views.styles),
    path('justDeleteAll/',views.deleteAll),
]
