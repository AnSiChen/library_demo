from django.contrib import admin
from .models import Book, Genre, Profile, UserBook, Review, ReadingChallenge, QuickNote

admin.site.register(Book)
admin.site.register(Genre)
admin.site.register(Profile)
admin.site.register(UserBook)
admin.site.register(Review)
admin.site.register(ReadingChallenge)
admin.site.register(QuickNote)