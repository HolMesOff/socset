from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import UserSerializer, LoginSerializer, FriendshipSerializer, FriendRequestSerializer, PostSerializer
from .models import User, FriendRequest, Friendship, Post
from django.shortcuts import get_object_or_404

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        # Получаем данные из запроса
        username = request.data.get('username')
        password = request.data.get('password')

        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)

        # Если аутентификация не удалась, возвращаем ошибку
        if user is None:
            return Response({"error": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        # Получаем или создаем токен для пользователя
        token, created = Token.objects.get_or_create(user=user)

        # Возвращаем токен, имя пользователя и user_id (из уже аутентифицированного пользователя)
        return Response({
            "token": token.key,
            "username": user.username,  # Используем username пользователя из базы
            "user_id": user.id          # Используем id пользователя из базы
        }, status=status.HTTP_200_OK)

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username', None)
        if not username:
            return Response({"detail": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем текущего пользователя
        current_user = request.user

        # 1. Попробуем сначала найти точного пользователя
        exact_user = User.objects.filter(username=username).exclude(id=current_user.id).first()

        if exact_user:  # Если точный пользователь найден
            serializer = UserSerializer(exact_user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 2. Если точного пользователя нет, ищем похожие ники
        users = User.objects.filter(username__icontains=username).exclude(id=current_user.id)

        if not users.exists():  # Если нет похожих пользователей
            return Response({"detail": "No users found"}, status=status.HTTP_404_NOT_FOUND)

        # Если есть похожие пользователи
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        to_user = get_object_or_404(User, id=id)

        if request.user == to_user:
            return Response({"error": "Вы не можете отправить запрос на добавление в друзья самому себе"},
                            status=status.HTTP_400_BAD_REQUEST)

        if Friendship.objects.filter(user=request.user, friend=to_user).exists() or \
                Friendship.objects.filter(user=to_user, friend=request.user).exists():
            return Response({"error": "Вы уже дружите с этим пользователем"}, status=status.HTTP_400_BAD_REQUEST)

        friend_request, created = FriendRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )

        if created:
            return Response({"message": "Заявка на добавление в друзья прошла успешно!"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Заявка на добавление в друзья уже имеется!"}, status=status.HTTP_200_OK)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, from_user_id):
        from_user = get_object_or_404(User, id=from_user_id)

        if request.user == from_user:
            return Response({"error": "Вы не можете принять запрос на добавление в друзья от самого себя"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            friend_request = FriendRequest.objects.get(from_user=from_user, to_user=request.user)
        except FriendRequest.DoesNotExist:
            return Response({"error": "Запрос на добавления в друзья не существует!"}, status=status.HTTP_404_NOT_FOUND)

        if Friendship.objects.filter(user=request.user, friend=from_user).exists() or Friendship.objects.filter(
                user=from_user, friend=request.user).exists():
            return Response({"error": "Дружба уже существует!"}, status=status.HTTP_400_BAD_REQUEST)

        Friendship.objects.create(
            user=request.user,
            friend=from_user
        )
        Friendship.objects.create(
            user=from_user,
            friend=request.user
        )

        friend_request.delete()
        return Response({"message": "Заявка в друзья успешно принята!"}, status=status.HTTP_200_OK)


class DeclineFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, from_user_id):
        # Получаем пользователя, который отправил запрос
        from_user = get_object_or_404(User, id=from_user_id)

        try:
            # Ищем заявку в друзья, отправленную этим пользователем текущему
            friend_request = FriendRequest.objects.get(from_user=from_user, to_user=request.user)
        except FriendRequest.DoesNotExist:
            return Response({"error": "Заявка в друзья не найдена."}, status=status.HTTP_404_NOT_FOUND)

        # Удаляем заявку
        friend_request.delete()
        return Response({"message": "Заявка в друзья отклонена."}, status=status.HTTP_200_OK)



class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, friend_id):
        friend = get_object_or_404(User, id=friend_id)

        friendship = Friendship.objects.filter(user=request.user, friend=friend).first()
        reverse_friendship = Friendship.objects.filter(user=friend, friend=request.user).first()

        if friendship or reverse_friendship:
            if friendship:
                friendship.delete()
            if reverse_friendship:
                reverse_friendship.delete()

            return Response({"message": "Друг успешно удален"}, status=status.HTTP_200_OK)

        return Response({"error": "Дружбы не существует!"}, status=status.HTTP_404_NOT_FOUND)

class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recipient_id):
        recipient = get_object_or_404(User, id=recipient_id)
        data = request.data.copy()
        data['recipient'] = recipient.id

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save(sender=request.user, recipient=recipient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserMessagesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        sent_messages = Message.objects.filter(sender=self.request.user)
        received_messages = Message.objects.filter(recipient=self.request.user)

        sent_users = sent_messages.values('recipient').distinct()
        received_users = received_messages.values('sender').distinct()
        all_user_ids = list(sent_users) + list(received_users)
        unique_user_ids = {user['recipient'] if 'recipient' in user else user['sender'] for user in all_user_ids}

        return User.objects.filter(id__in=unique_user_ids)




from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Message
from .serializers import MessageSerializer


from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends = Friendship.objects.filter(user=user).values_list('friend', flat=True)
        posts_from_user = Post.objects.filter(author=user)
        posts_from_friends = Post.objects.filter(author__in=friends)
        posts = posts_from_user | posts_from_friends
        return posts

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не можете удалить чужой пост.")
        instance.delete()

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        # Если пользователь уже поставил лайк, возвращаем ошибку
        if post.likes.filter(id=user.id).exists():
            return Response({'detail': 'Вы уже лайкнули этот пост.'}, status=status.HTTP_400_BAD_REQUEST)

        # Добавляем лайк
        post.likes.add(user)

        return Response({'detail': 'Пост лайкнут!'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        post = self.get_object()
        user = request.user

        # Если пользователь не поставил лайк, возвращаем ошибку
        if not post.likes.filter(id=user.id).exists():
            return Response({'detail': 'Вы не лайкали этот пост.'}, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем лайк
        post.likes.remove(user)

        return Response({'detail': 'Лайк удален.'}, status=status.HTTP_204_NO_CONTENT)

class UnlikePostView(APIView):
    def post(self, request, post_id):
        user = request.user  # Получаем текущего авторизованного пользователя
        try:
            post = Post.objects.get(id=post_id)  # Находим пост по ID
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, поставил ли пользователь лайк этому посту
        if user in post.likes.all():
            post.likes.remove(user)  # Убираем лайк
            return Response({'detail': 'Like removed.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Like not found.'}, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        recipient_id = self.kwargs.get('recipient_id')

        received_messages = Message.objects.filter(
            recipient=self.request.user,
            sender_id=recipient_id
        )

        sent_messages = Message.objects.filter(
            sender=self.request.user,
            recipient_id=recipient_id
        )

        combined_messages = list(received_messages) + list(sent_messages)

        unique_messages = {message.id: message for message in combined_messages}.values()

        sorted_messages = sorted(unique_messages, key=lambda x: x.timestamp)

        return sorted_messages

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if len(queryset) == 0:
            return Response({"error": "Диалога не существует!"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)




class FriendshipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        user = self.request.user
        # Показываем дружбы, где текущий пользователь — либо `user`, либо `friend`
        return Friendship.objects.filter(user=user) | Friendship.objects.filter(friend=user)


class FriendRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        user = self.request.user
        # Показываем запросы на дружбу, отправленные текущим пользователем или полученные от других
        return FriendRequest.objects.filter(from_user=user) | FriendRequest.objects.filter(to_user=user)
