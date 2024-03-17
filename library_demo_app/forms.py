from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Book, Profile, Review, UserBook, QuickNote

class ExtendedSignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    bio = forms.CharField(max_length=500, required=False)
    location = forms.CharField(max_length=100, required=False)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super(ExtendedSignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['id'] = 'id_password1'
        self.fields['password2'].widget.attrs['id'] = 'id_password2'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'bio', 'location', 'birth_date') 

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                bio=self.cleaned_data['bio'],
                location=self.cleaned_data['location'],
                birth_date=self.cleaned_data['birth_date'],
            )
        return user
    
class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(choices=[(num, num) for num in range(1, 6)], widget=forms.RadioSelect)

    class Meta:
        model = Review
        fields = ['rating', 'comment']

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'pages', 'genres', 'publication_date', 'cover_image', 'summary']
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
            'genres': forms.CheckboxSelectMultiple(),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'birth_date', 'profile_photo']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

class UserBookForm(forms.ModelForm):
    class Meta:
        model = UserBook
        fields = ['read', 'progress']

class QuickNoteForm(forms.ModelForm):
    class Meta:
        model = QuickNote
        fields = ['note']   
