from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Category, Comment, Genre, GenreTitle, Review, Title

User = get_user_model()

admin.site.register(User)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(Category)
admin.site.register(Review)
admin.site.register(Comment)
admin.site.register(GenreTitle)
