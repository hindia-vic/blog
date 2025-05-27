from django.urls import path

from .views import post_detail,post_list,post_share,post_comment,post_search,register,post_create,delete_post,confirm_delete,update_post,user_profile,profile_edit,post_draft_list,contact,reading_list,add_to_reading_list,remove_from_reading_list,post_draft_list,draft_detail,comment_delete,comment_edit
from  .feeds import LatestPostsFeed
#from . import views
app_name='blog'
urlpatterns=[
    path('',post_list,name='post_list'),
    path('tag/<slug:tag_slug>/',post_list, name='post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/',post_detail,name='post_detail'),
    path('<int:post_id>/share/',post_share,name='post_share'),
    path('<int:post_id>/comment/',post_comment, name='post_comment'),
     path('comment/<int:pk>/delete/', comment_delete, name='comment_delete'),
     path('comment/<int:pk>/edit/',comment_edit, name='comment_edit'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', post_search, name='post_search'),
    path('create/',post_create,name='post_create'),
    path('register',register,name='register'),
    path('posts/<int:post_id>/delete/confirm/',confirm_delete, name='post_confirm_delete'),
    path('<int:post_id>/delete/',delete_post, name='post_delete'),
    path('<int:post_id>/update/',update_post,name='update'),
    path('profile/', user_profile, name='user_profile'),
    path('profile/edit/',profile_edit, name='profile_edit'),
    path('draft/',post_draft_list,name='drafts'),
    path('contact/', contact, name='contact'),
    path('reading-list/', reading_list, name='reading_list'),
    path('reading-list/add/<int:post_id>/', add_to_reading_list, name='add_to_reading_list'),
    path('reading-list/remove/<int:post_id>/', remove_from_reading_list, name='remove_from_reading_list'),
    path('draft/', post_draft_list, name='drafts'),
    path('draft/<int:pk>/', draft_detail, name='draft_detail'),
]
