from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13)
    pages = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, blank=True) 
    publication_date = models.DateField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    summary = models.TextField(blank=True) 

    def __str__(self):
        return self.title
    
class UserBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    progress = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Whether a book should be hidden from public profile 
    hide_from_profile = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Review(models.Model):
    user_book = models.ForeignKey(UserBook, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.user_book.book.title}"
    
class ReadingChallenge(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    goal = models.IntegerField(default=50)  # User can change 
    progress = models.IntegerField(default=0)  # Tracks number of books read

    def __str__(self):
        return f"{self.user.username}'s Reading Challenge"
    
class QuickNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Note"