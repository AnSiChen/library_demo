import requests
import os
import io
import imgkit
import random
import json
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from .forms import ExtendedSignUpForm, BookForm, ProfileForm, ReviewForm, QuickNoteForm
from .models import Book, UserBook, Review, Genre, ReadingChallenge, User, Profile, QuickNote
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.views import LoginView as AuthLoginView
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.staticfiles import finders #Reference
from django.templatetags.static import static #Refrence
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError



class CustomLoginView(AuthLoginView):
    def form_valid(self, form):
        messages.success(self.request, 'You have successfully logged in.')
        return super().form_valid(form)
    
@require_http_methods(["POST"])
def custom_logout(request):
    logout(request)
    return redirect('home')
    
@require_http_methods(["POST"])
def validate_user_password(request):

    data = json.loads(request.body)
    password = data.get('password')

    try:
        # Use Django's password validators
        validate_password(password)
        return JsonResponse({'valid': True})
    except ValidationError as e:
        # Return the error messages if password is invalid
        return JsonResponse({'valid': False, 'errors': e.messages})

def general_book_search(request):
    query = request.GET.get('q', '')
    books = None

    if query:
        books = Book.objects.filter(
            title__icontains=query) | Book.objects.filter(
            author__icontains=query) | Book.objects.filter(
            isbn__icontains=query)
    else:
        books = Book.objects.none() # books is an empty QuerySet, not None

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        results = [{"title": book.title, "id": book.id} for book in books]
        return JsonResponse({"results": results}, content_type="application/json")
    
    return render(request, 'tracker/general_book_search.html', {'books': books, 'query': query})

def explore_books(request):
    books = list(Book.objects.all()) # Retrieve all books from the database
    random.shuffle(books)
    return render(request, 'tracker/explore_books.html', {'books': books})

@login_required
def book_list(request):
    # Fetch the UserBook instances for the current user
    user_books = UserBook.objects.filter(user=request.user)

    # Passing user_books directly to the template
    return render(request, 'tracker/book_list.html', {'user_books': user_books})

@require_POST
@login_required
def add_to_my_list(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # Check for duplicates
    if UserBook.objects.filter(user=request.user, book=book).exists():
        message = "You already have this book in your list."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "error", "message": message})
        messages.error(request, message)
        return redirect('general_book_search')

    # Create a new UserBook object and save the reference to it
    new_user_book = UserBook.objects.create(user=request.user, book=book)
    message = "Book added to your list."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "status": "added", 
            "message": "Book added to your list.", 
            "user_book_id": new_user_book.id
        })

    messages.success(request, message)
    return redirect('book_list')


def home(request):
    # Get a random set of books 
    books = list(Book.objects.all())
    random_books = random.sample(books, min(len(books), 10)) if books else []

    reading_challenge = None
    if request.user.is_authenticated:
        user = request.user
        reading_challenge, created = ReadingChallenge.objects.get_or_create(user=user)
        progress = UserBook.objects.filter(user=user, read=True).count()
        reading_challenge.progress = progress
        reading_challenge.save()

    return render(request, 'tracker/home.html', {
        'reading_challenge': reading_challenge,
        'random_books': random_books # Show random books in template
    })

def signup(request):
    if request.method == 'POST':
        form = ExtendedSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'You have successfully signed up.')
            return redirect('home')
    else:
        form = ExtendedSignUpForm()
    return render(request, 'tracker/signup.html', {'form': form})

@login_required
def dashboard(request):
    in_progress_books = UserBook.objects.filter(user=request.user, read=False, progress__gt=0)[:5]
    current_user_profile = request.user.profile
    profiles = Profile.objects.exclude(user=request.user)  # Exclude the current user's profile
    user_profiles = list(User.objects.exclude(id=request.user.id).exclude(username='').exclude(is_superuser=True))
    random_profiles = random.sample(user_profiles, min(len(user_profiles), 2))

    quick_notes = QuickNote.objects.filter(user=request.user).order_by('-created_at')
    if request.method == 'POST':
        form = QuickNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            # Redirect to prevent resubmission if the user refreshes the page
            return redirect('dashboard')
    else:
        form = QuickNoteForm()

        from django.http import JsonResponse


    return render(request, 'tracker/dashboard.html', {
        'in_progress_books': in_progress_books,
        'current_user_profile': current_user_profile,
        'random_profiles': random_profiles,
        'profiles': profiles,
        'quick_notes': quick_notes,
        'note_form': form,
    })

@login_required
def add_quick_note(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = QuickNoteForm(request.POST)
        if form.is_valid():
            quick_note = form.save(commit=False)
            quick_note.user = request.user
            quick_note.save()
            return JsonResponse({
                'status': 'success',
                'note': quick_note.note,
                'created_at': quick_note.created_at.strftime('%Y-%m-%d %H:%M')
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()})
    return JsonResponse({'status': 'failed'}, status=400)

@login_required
def user_profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    # Get the user's profile based on the username
    profile_user = User.objects.get(username=username)
    user_books = UserBook.objects.filter(user=profile_user)

    # Determine which books to show the "Add Book" button for
    current_user_book_ids = request.user.userbook_set.all().values_list('book_id', flat=True)
    books_to_add = user_books.exclude(book_id__in=current_user_book_ids)

    #filter out hidden books
    user_books = UserBook.objects.filter(user=profile_user, hide_from_profile=False)

    return render(request, 'tracker/user_profile.html', {
        'profile_user': profile_user,
        'user_books': user_books,
        'books_to_add': books_to_add,
        'current_user_book_ids': current_user_book_ids,
    })

@login_required
@require_POST
def toggle_book_visibility(request, user_book_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_book = get_object_or_404(UserBook, pk=user_book_id, user=request.user)

        user_book.hide_from_profile = not user_book.hide_from_profile
        user_book.save()

        return JsonResponse({'success': True, 'new_state': user_book.hide_from_profile})
    else:
        return JsonResponse({'success': False})



def fetch_book_details(isbn):
    url = f'https://openlibrary.org/isbn/{isbn}.json'
    response = requests.get(url)
    if response.ok:
        book_data = response.json()
        # Extract author keys
        author_keys = [author['key'] for author in book_data.get('authors', [])]
        return book_data, author_keys
    else:
        return None, []
    
def fetch_author_details(author_key):
    """
    Fetches the author's details from the Open Library API given the author's key.
    """
    base_url = "https://openlibrary.org"
    author_url = f"{base_url}{author_key}.json"
    response = requests.get(author_url)
    if response.ok:
        author_data = response.json()
        return author_data.get("name")
    else:
        return None  

@login_required
def add_book(request):
    KNOWN_MULTI_WORD_GENRES = [
        'Literary Fiction', 'Historical Fiction', 'Science Fiction',
        'Young Adult (YA)', 'Children\'s Fiction', 'Health & Wellness',
        'Business & Economics', 'True Crime', 'Art & Photography',
        'Religion & Spirituality', 'Graphic Novels'
    ]

    cover_image_url = None

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book_instance = form.save(commit=False)

            # Check if a cover image URL was saved in the session
            session_cover_image_url = request.session.pop('cover_image_url', None)
            if session_cover_image_url:
                response = requests.get(session_cover_image_url)
                if response.status_code == 200:
                    book_instance.cover_image.save(os.path.basename(session_cover_image_url), ContentFile(response.content))

            book_instance.save()
            form.save_m2m()  # Save many-to-many fields like genres
            # Create a UserBook instance
            UserBook.objects.create(user=request.user, book=book_instance, read=False)
            messages.success(request, 'Book added to your list successfully!')
            return redirect('book_list')
        else:
            messages.error(request, 'There was an error adding the book.')

    else:  # GET request
        isbn = request.GET.get('isbn')
        form = BookForm()
        if isbn:
            # Remove dashes from the ISBN
            isbn = isbn.replace('-', '')

            book_data, author_keys = fetch_book_details(isbn)
            if book_data:
                authors = [fetch_author_details(key) for key in author_keys if key]
                genre_instances = process_genres(book_data.get('subjects', []), KNOWN_MULTI_WORD_GENRES)
                cover_id = book_data.get('covers', [None])[0]
                cover_image, cover_image_url = download_and_verify_image(cover_id) if cover_id else (None, None)
                
                initial_data = {
                    'title': book_data.get('title'),
                    'author': ', '.join(authors),
                    'isbn': isbn,
                    'pages': book_data.get('pagination'),
                    'publication_date': book_data.get('publish_date') + "-01-01" if book_data.get('publish_date') else None,
                }
                form = BookForm(initial=initial_data)
                form.fields['genres'].initial = [genre.id for genre in genre_instances]

                if cover_image_url:
                    # Save the cover image URL in the session for later use
                    request.session['cover_image_url'] = cover_image_url
            else:
                messages.error(request, 'No book data found for the provided ISBN.')

    return render(request, 'tracker/add_book.html', {
        'form': form,
        'cover_image_url': cover_image_url,
    })

def process_genres(api_genres, known_multi_word_genres):
    genre_instances = []
    for genre_string in api_genres:
        if genre_string in known_multi_word_genres:
            genre, created = Genre.objects.get_or_create(name=genre_string)
            genre_instances.append(genre)
        else:
            genre_names = genre_string.split(',')
            for genre_name in genre_names:
                genre_name = genre_name.strip()
                if genre_name:
                    genre, created = Genre.objects.get_or_create(name=genre_name)
                    genre_instances.append(genre)
    return genre_instances

def download_and_verify_image(cover_id):
    cover_image_url = f'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg'
    response = requests.get(cover_image_url)
    if response.status_code == 200:
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(response.content)
        img_temp.flush()

        try:
            img = Image.open(img_temp.name)
            img.verify()  # Verify that it's a valid image
            img_temp.seek(0)  # Seek to the start of the file
            cover_image = ContentFile(img_temp.read(), name=f"cover_{cover_id}.jpg")
            return cover_image, cover_image_url
        except (IOError, ValueError):
            return None, cover_image_url
        finally:
            img_temp.close()
    else:
        return None, None



@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    user_book = UserBook.objects.filter(user=request.user, book=book).first()
    reviews = Review.objects.filter(user_book__book=book)
    
    # Check if the current user has already submitted a review for this book
    has_reviewed = Review.objects.filter(user_book__book=book, user_book__user=request.user).exists()
    
    # Only pass the form if the user has not reviewed
    review_form = ReviewForm() if not has_reviewed else None

    return render(request, 'tracker/book_detail.html', {
        'book': book, 
        'user_book': user_book, 
        'reviews': reviews,
        'form': review_form,  # This will be None if the user has already reviewed
        'has_reviewed': has_reviewed  # Pass this to the template to control form display
    })


@login_required
def edit_book(request, user_book_id):
    user_book = get_object_or_404(UserBook, id=user_book_id, user=request.user)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=user_book.book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=user_book.book)
    return render(request, 'tracker/edit_book.html', {'form': form})

#Renamed in FRONT-END to Remove, backend remains the same; does NOT delete the book from database, just removes it from the user's personal book list
@login_required
def delete_book(request, user_book_id):
    user_book = get_object_or_404(UserBook, id=user_book_id, user=request.user)
    if request.method == 'POST':
        user_book.delete()
        return redirect('book_list')
    return render(request, 'tracker/confirm_delete.html', {'book': user_book.book})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'tracker/edit_profile.html', {'form': form})

@login_required
def update_read_status(request, user_book_id):
    user_book = get_object_or_404(UserBook, id=user_book_id, user=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status == 'Not Started':
            read_status = False
            progress = 0
        elif status == 'In Progress':
            read_status = False
            progress = request.POST.get('progress', 0)
        elif status == 'Completed':
            read_status = True
            progress = 100
        else:
            # Handle unexpected status value
            return JsonResponse({"status": "error", "message": "Invalid read status."}, status=400)

        user_book.read = read_status
        user_book.progress = min(max(int(progress), 0), 100)  # Ensure progress is between 0 and 100
        user_book.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "message": "Read status and progress updated."})
        
        messages.success(request, 'Read status and progress updated.')
        return redirect('book_list')
    
    return redirect('book_list')




@login_required
def submit_review(request, user_book_id):
    user_book = get_object_or_404(UserBook, pk=user_book_id, user=request.user)

    if not user_book.read:
        message = "You can only review books you've read."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "error", "message": message})
        messages.error(request, message)
        return redirect('book_detail', book_id=user_book.book.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user_book = user_book
            review.user = request.user
            review.save()
            review_data = {
                "user": review.user.username,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at.strftime('%Y-%m-%d %H:%M:%S') 
            }

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"status": "success", "new_review": review_data})

            messages.success(request, "Review submitted successfully.")
            return redirect('book_detail', book_id=user_book.book.id)

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Handle form errors in AJAX
                return JsonResponse({"status": "error", "errors": form.errors.as_json()})
            # If not an AJAX request, re-render the page with the form and its errors
            return render(request, 'book_detail.html', {'form': form, 'user_book': user_book})

    # If it's not a POST request, redirect to the book detail page.
    return redirect('book_detail', book_id=user_book.book.id)


@login_required
def generate_book_card(request, book_id):
    # Fetch the book using the provided ID
    book = get_object_or_404(Book, id=book_id)

    # Fetch the UserBook instance
    #user_book = UserBook.objects.filter(user=request.user, book=book).first()
    #if not user_book:
        # If no UserBook instance is found, handle this case appropriately
       #return HttpResponse("No review found for this book.", status=404)
    
    """ NOT IN USE, KEPT FOR REFRENCE
    # Fetch the review for the UserBook instance
    review = Review.objects.filter(user_book=user_book).first()
    if not review:
        # If no review is found, handle this case
        # You might want to show a message that there's no review
        return HttpResponse("No review found for this book.", status=404)
    """

    # Check if the book has a cover image and create the absolute URL
    if book.cover_image:
        cover_image_url = request.build_absolute_uri(book.cover_image.url)
    else:
        cover_image_url = None  # Or set a default image URL

    # Render the HTML for the book card
    html = render_to_string('tracker/shareable_book_card.html', {
        'book': book,
        # 'review': review,
        'cover_image_url': cover_image_url,
        'website_name': 'BookTracker.project'
    })

   # Convert HTML to Image and get the image as bytes
    image_bytes = html_to_image(html)  # html_to_image now returns bytes

    # Write the image bytes to the buffer
    buffer = io.BytesIO(image_bytes)

    # Create a response with the image
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response['Content-Disposition'] = 'attachment; filename="book_card.png"'
    return response

def html_to_image(html):
    options = {
        'format': 'png',
        'encoding': "UTF-8",
    }

    img = imgkit.from_string(html, False, options=options)
    return img

@login_required
def reading_challenge_view(request):
    user = request.user
    reading_challenge, created = ReadingChallenge.objects.get_or_create(user=user) #REference: created 

    if request.method == 'POST':
        new_goal = int(request.POST.get('new_goal', 0))
        reading_challenge.goal = new_goal
        reading_challenge.save()
        
        progress = UserBook.objects.filter(user=user, read=True).count()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'new_goal': reading_challenge.goal,
                'progress': progress,
                'congratulations': progress >= reading_challenge.goal
            })

        return redirect('home')

    progress = UserBook.objects.filter(user=user, read=True).count()
    reading_challenge.progress = progress
    reading_challenge.save()

    return render(request, 'tracker/home.html', {
        'reading_challenge': reading_challenge
    })

#