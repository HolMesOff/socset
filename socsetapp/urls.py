from django.urls import path, include
from .views import SendMessageView, UserMessagesView, MessageDetailView, RegisterView, LoginView, RemoveFriendView, SendFriendRequestView, AcceptFriendRequestView, DeclineFriendRequestView
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet, FriendRequestViewSet, PostViewSet, UnlikePostView, UserSearchView

router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')
router.register(r'friend-requests', FriendRequestViewSet, basename='friendrequest')
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),

    path('send-friend-request/<int:id>/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('remove-friend-request/<int:friend_id>/', RemoveFriendView.as_view(), name='RemoveFriendView'),
    path('accept-friend-request/<int:from_user_id>/', AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('decline-friend-request/<int:from_user_id>/', DeclineFriendRequestView.as_view(), name='decline_friend_request'),

    path('send_message/<int:recipient_id>/', SendMessageView.as_view(), name='send_message'),
    path('messages/', UserMessagesView.as_view(), name='user-messages'),
    path('messages/<int:recipient_id>/', MessageDetailView.as_view(), name='message-detail'),

    path('request/', include(router.urls)),
    path('posts/<int:post_id>/unlike/', UnlikePostView.as_view(), name='unlike-post'),
]