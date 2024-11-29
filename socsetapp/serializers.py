from rest_framework import serializers
from .models import User,Friendship, FriendRequest, Message, Post
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'profile_picture')

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer2(serializers.ModelSerializer):
    profile_picture = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


User = get_user_model()

class FriendshipSerializer(serializers.ModelSerializer):
    user = UserSerializer2()
    friend = UserSerializer2()

    class Meta:
        model = Friendship
        fields = ['user', 'friend', 'created_at']

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.StringRelatedField()
    to_user = serializers.StringRelatedField()

    class Meta:
        model = FriendRequest
        fields = ['from_user', 'to_user', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'content', 'timestamp', 'is_read']
        read_only_fields = ['id', 'sender', 'timestamp', 'is_read']


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at', 'likes', 'like_count']