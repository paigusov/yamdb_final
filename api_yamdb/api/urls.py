from api.v1.views import (CategoryViewSet, CommentViewSet,
                          ConfirmationCodeTokenView, GenreViewSet,
                          ReviewViewSet, SignUpView, TitleViewSet,
                          UsersViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

v1_router = DefaultRouter()

v1_router.register('users', UsersViewSet)
v1_router.register('titles', TitleViewSet, basename='titles')
v1_router.register('genres', GenreViewSet, basename='genres')
v1_router.register('categories', CategoryViewSet, basename='categories')
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='reviews'
)
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments',
)

auth = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', ConfirmationCodeTokenView.as_view(), name='token'),
]

v1_urls = [
    path('', include(v1_router.urls)),
    path('auth/', include(auth)),
]


urlpatterns = [path('v1/', include(v1_urls))]
