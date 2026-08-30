from django.urls import path 
from . import views




app_name = 'session'

urlpatterns = [
  path("create/<str:file_number>/",views.create_session,name="create_session"),
  path("<int:session_id>/", views.session_detail, name="session_detail"),
  path("<int:session_id>/join/", views.join_session, name="join_session"),
  path("<int:session_id>/respond/", views.respond_session, name="respond_session"),
  path("<int:session_id>/specialist-respond/",views.specialist_respond_session,name="specialist_respond_session"),
  path("<int:session_id>/complete/",views.complete_session,name="complete_session"),
  path("<int:session_id>/add-note/", views.add_session_note, name="add_session_note"),
  path("<int:session_id>/notes/", views.session_note_detail, name="session_note_detail"),
  path("<int:session_id>/cancel/",views.cancel_session,name="cancel_session"),



]

