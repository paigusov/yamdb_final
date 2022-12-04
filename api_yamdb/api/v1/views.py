from api.v1.filters import TitleFilter
from api.v1.permissions import (AdminOnlyPermission,
                                IsAdminOrReadOnlyPermission,
                                IsAuthorAdminModeratorOrReadOnly)
from api.v1.serializers import (CategorySerializer, CommentSerializer,
                                ConfirmationCodeTokenSerializer,
                                GenreSerializer, ReviewSerializer,
                                SelfUserSerializer, TitleGetSerializer,
                                TitlePostSerializer, UserSerializer)
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, generics, mixins, pagination, permissions,
                            serializers, status, viewsets)
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenViewBase
from reviews.models import Category, Genre, Review, Title
from users.models import User

from api_yamdb.settings import DEFAULT_SENDER_EMAIL


class CreateListDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAdminOrReadOnlyPermission]
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = PageNumberPagination


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnlyPermission]
    pagination_class = PageNumberPagination
    queryset = Title.objects.annotate(rating=Avg('reviews__score')).order_by(
        'name'
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleGetSerializer
        return TitlePostSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    )
    pagination_class = PageNumberPagination
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(title=title, author=self.request.user)

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return title.reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    )
    pagination_class = PageNumberPagination

    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        serializer.save(review=review, author=self.request.user)

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        review = get_object_or_404(
            title.reviews.all(), pk=self.kwargs.get('review_id')
        )
        return review.comments.all()


class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    email_subject = 'Confirmation code'
    email_message = (
        'Привет, {username}! Регистрация на YaMDB успешна выполнена. '
        'Твой код подтверждения для входа: {code}. '
    )

    def send_confirmation_code(self, user: User, code: int):
        send_mail(
            subject=self.email_subject,
            message=self.email_message.format(
                username=user.username, code=code
            ),
            recipient_list=[user.email],
            from_email=DEFAULT_SENDER_EMAIL,
        )

    def post(self, request: Request):
        response = super().post(request)

        user: User = get_object_or_404(
            User, username=response.data['username']
        )
        code = default_token_generator.make_token(user)
        self.send_confirmation_code(user, code)

        data = {
            'username': response.data['username'],
            'email': response.data['email'],
        }
        return Response(data, status=status.HTTP_200_OK)


class ConfirmationCodeTokenView(TokenViewBase):
    serializer_class = ConfirmationCodeTokenSerializer
    token_class = AccessToken
    error_message = {
        'invalid_code': (
            'Нет активных аккаунтов с таким кодом подтверждения. '
        )
    }

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)

    def post(self, request, *args, **kwargs):
        serializer: serializers.Serializer = self.get_serializer(
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        username, confirmation_code = serializer.validated_data.values()
        user: User = get_object_or_404(User, username=username)

        if not default_token_generator.check_token(user, confirmation_code):
            return Response(self.error_message, status.HTTP_400_BAD_REQUEST)

        token = self.get_token(user)
        response_data = {'token': str(token)}
        return Response(response_data, status=status.HTTP_200_OK)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AdminOnlyPermission]
    pagination_class = pagination.PageNumberPagination
    lookup_field = 'username'

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=SelfUserSerializer,
    )
    def me(self, request: Request):
        instance = self.request.user

        if request.method == 'GET':
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
