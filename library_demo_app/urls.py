from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import add_book, edit_profile, update_read_status, general_book_search, add_to_my_list, generate_book_card, reading_challenge_view, explore_books, user_profile

urlpatterns = [
    path('', views.home, name='home'),  # This is the root URL
    path('books/', views.book_list, name='book_list'),  
    path('search/', general_book_search, name='general_book_search'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_book/', add_book, name='add_book'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/edit/<int:user_book_id>/', views.edit_book, name='book_edit'),
    # delete_book Renamed in FRONT-END to Remove, backend remains the same; does NOT delete the book from database
    path('books/delete/<int:user_book_id>/', views.delete_book, name='book_delete'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('books/review/<int:user_book_id>/', views.submit_review, name='submit_review'),
    path('books/update_read_status/<int:user_book_id>/', update_read_status, name='update_read_status'),
    path('add-to-my-list/<int:book_id>/', add_to_my_list, name='add_to_my_list'),
    path('generate_book_card/<int:book_id>/', generate_book_card, name='generate_book_card'),
    path('reading_challenge/', reading_challenge_view, name='reading_challenge'),
    path('explore/', explore_books, name='explore_books'),
    path('validate-password/', views.validate_user_password, name='validate_password'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('books/toggle_visibility/<int:user_book_id>/', views.toggle_book_visibility, name='toggle_book_visibility'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('add_quick_note/', views.add_quick_note, name='add_quick_note'),

]