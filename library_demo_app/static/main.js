
// Main 
document.addEventListener('DOMContentLoaded', function() {
    // Live search listener
    const searchInput = document.getElementById('book-search');
    const resultsContainer = document.getElementById('search-results');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value;
            // Hide and clear the container if the query is empty
            if (!query) {
                resultsContainer.style.display = 'none';
                resultsContainer.innerHTML = '';
                return; // Exit the function early
            }

            // Perform the AJAX fetch for the live search
            fetch(`/search/?q=${query}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Show the container when there are results
                resultsContainer.style.display = 'block';
                resultsContainer.innerHTML = ''; // Clear existing results

                if (data.results.length === 0) {
                    resultsContainer.innerHTML = '<div>No results found</div>';
                } else {
                    data.results.forEach(book => {
                        // Create a link for each book and append it to the results container
                        const bookLink = document.createElement('a');
                        bookLink.href = `/books/${book.id}/`; // Link to book detail page
                        bookLink.textContent = book.title;
                        bookLink.classList.add('search-result-item');
                        resultsContainer.appendChild(bookLink);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Handle the error, e.g., show an error message to the user
            });
        });
    }

    // Search form submission prevention
    const searchForm = document.querySelector('form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            console.log('Search submitted!');
            event.preventDefault();
        });
    }

    // Update reading status function
    const readStatusForm = document.getElementById('read-status-form');

    if (readStatusForm) {
        readStatusForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the default form submission

            const userBookId = this.querySelector('select[id^="read-status-selector"]').id.split('_')[1];
            const readStatus = this.querySelector(`#read-status-selector_${userBookId}`).value;
            const progressInput = document.querySelector(`#progress_${userBookId}`);
            const progressBar = document.getElementById(`progress-bar_${userBookId}`);
            let progressValue = progressInput ? progressInput.value : 0;

            // Adjust progress based on read status and update the progress bar visually
            switch (readStatus) {
                case 'Not Started':
                    progressValue = 0;
                    progressBar.style.width = '0%';
                    progressInput.classList.remove('show');
                    break;
                case 'In Progress':
                    progressBar.style.width = `${progressValue}%`;
                    progressInput.classList.add('show');
                    break;
                case 'Completed':
                    progressValue = 100;
                    progressBar.style.width = '100%';
                    progressInput.classList.remove('show');
                    break;
            }

            // AJAX call to update the read status
            const formData = new FormData(this);
            formData.append('status', readStatus);
            formData.append('progress', progressValue);
            formData.append('csrfmiddlewaretoken', csrftoken); // Add CSRF token from a global variable

            fetch(`/books/update_read_status/${userBookId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken 
                },
                body: formData // Send the form data
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Read status and progress updated.');
                    // Show a success message to the user
                } else {
                    console.error('Error updating status:', data.message);
                }
            })
            .catch(error => {
                console.error('There was an error updating the read status:', error);
                // Show an error message to the user
            });
        });
    }
        

        // Add event listeners to the read-status-selector to show/hide progress input
        document.querySelectorAll('select[id^="read-status-selector"]').forEach(function(selector) {
            selector.addEventListener('change', function() {
                const userBookId = this.id.split('_')[1];
                const progressInput = document.querySelector(`#progress_${userBookId}`);
                const progressBar = document.querySelector(`#progress-bar_${userBookId}`);
                const selectedValue = this.value;

                if (selectedValue === 'In Progress') {
                    progressInput.classList.remove('hidden');
                    progressInput.classList.add('visible');
                } else {
                    progressInput.classList.remove('visible');
                    progressInput.classList.add('hidden');
                }

                if (selectedValue === 'Completed') {
                    progressBar.style.width = '100%';
                } else if (selectedValue === 'Not Started') {
                    progressBar.style.width = '0%';
                }
            });
        });

        // Add event listeners to the progress input to update the progress bar dynamically
        document.querySelectorAll('input[id^="progress"]').forEach(function(input) {
            input.addEventListener('input', function() {
                const userBookId = this.id.split('_')[1];
                const progressBar = document.querySelector(`#progress-bar_${userBookId}`);
                progressBar.style.width = this.value + '%';
            });
        });

        // Add to my list 

        document.querySelectorAll('.add-book-btn').forEach(function(button) {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const bookId = this.dataset.bookId;

                fetch(`/add-to-my-list/${bookId}/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'added') {
                        console.log(data.message);

                        // Find the container of the action buttons
                        const actionButtonsContainer = this.closest('.action-buttons');
                        if (actionButtonsContainer) {
                            // Assuming data.user_book_id contains the ID of the newly created UserBook
                            const userBookId = data.user_book_id;

                            // Construct the URLs based on your URL patterns
                            const editUrl = `/books/edit/${userBookId}/`;
                            const deleteUrl = `/books/delete/${userBookId}/`;
                            const shareableCardUrl = `/generate_book_card/${bookId}/`;

                            // Update the buttons
                            actionButtonsContainer.innerHTML = 
                            `<a href="${shareableCardUrl}" class="btn btn-secondary action-btn">Generate Shareable Card</a>` +
                            `<a href="${editUrl}" class="btn btn-primary action-btn">Edit</a>` +
                            `<a href="${deleteUrl}" class="btn btn-danger action-btn">Remove</a>`;
                        
                        }
                    } else {
                        console.error(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });


    // Submit review
    document.addEventListener('submit', function(e) {
        if (e.target && e.target.matches('.review-form')) {
            e.preventDefault();
            const userBookId = e.target.dataset.userBookId; // Use getAttribute to ensure you get the correct data

            fetch(`/books/review/${userBookId}/`, {
                method: 'POST',
                body: new FormData(e.target),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Add the new review to the DOM without reloading the page
                    const reviewsContainer = document.querySelector('.reviews');
                    const newReview = document.createElement('div');
                    newReview.classList.add('review');
                    newReview.innerHTML = `
                        <p><strong>${data.new_review.user}:</strong> ${data.new_review.comment} (Rating: ${data.new_review.rating})</p>
                        <p class="review-date">Date: ${data.new_review.created_at}</p>
                    `;
                    reviewsContainer.appendChild(newReview);

                    // Update the UI to reflect that the user has reviewed
                    e.target.style.display = 'none'; // Use e.target here since it's the form that triggered the submit event
                    const reviewStatus = document.querySelector('.review-status');
                    if (reviewStatus) {
                        reviewStatus.innerHTML = 'You have already submitted a review for this book.';
                    }
                } else {
                    // Handle form errors or other issues
                    console.error(data.errors);
                }
            })
            .catch(error => {
                console.error('Error during fetch:', error);
            });
        }
    });


    // Reading Challenge
    const challengeForm = document.getElementById('reading-challenge-form');
    const congratulationsMessage = document.getElementById('congratulations-message'); // Display message 

    if (challengeForm) {
        challengeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/reading_challenge/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken  
                }
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Update the goal and progress on the page
                    document.getElementById('reading-goal').textContent = data.new_goal;
                    document.getElementById('reading-progress').textContent = data.progress;
                    if (data.congratulations) {
                        congratulationsMessage.textContent = 'Congratulations on completing your challenge!';
                        congratulationsMessage.style.display = 'block'; // Show the message
                    } else {
                        congratulationsMessage.style.display = 'none'; // Hide the message
                    }
                } else {
                    console.error('Error:', data.message);
                }
            })
            .catch(error => {
                console.error('Error during fetch:', error);
            });
        });
    }


 

        // Swiper
        var swiper = new Swiper('.swiper-container', {
            initialSlide: 3,
            slidesPerView: 3,
            spaceBetween: 30,
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            
            autoplay: {
                delay: 2500,  // Delay in milliseconds between slides. Adjust as needed.
                disableOnInteraction: false, // Autoplay will not be disabled after user interactions
            },

            speed: 600,

    
            navigation: false,
            
            // Responsive breakpoints
            breakpoints: {
                // when window width is <= 499px
                499: {
                    slidesPerView: 2,
                    spaceBetweenSlides: 30
                },
                // when window width is <= 999px
                999: {
                    slidesPerView: 3,
                    spaceBetweenSlides: 40
                }
            }
        });

    

    // Password validation and matching live

    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const passwordError = document.getElementById('passwordError');
    
    if (password1 && password2 && passwordError) {
        let lastPasswordStrengthValid = true;
    // Function to validate password strength
    function validatePasswordStrength() {
        fetch('/validate-password/', {
            method: 'POST',
            body: JSON.stringify({ 'password': password1.value }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken 
            }
        })
        .then(response => response.json())
        .then(data => {
            lastPasswordStrengthValid = data.valid;
            updateErrorMessage();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    // Function to update the error message based on password strength and match
    function updateErrorMessage() {
        if (!lastPasswordStrengthValid) {
            // Show password strength error
            passwordError.textContent = "Password is too weak.";
            passwordError.style.display = 'block';
        } else if (password1.value !== password2.value) {
            // Show password mismatch error
            password2.setCustomValidity("Passwords don't match.");
            passwordError.textContent = "Passwords don't match.";
            passwordError.style.display = 'block';
        } else {
            // Clear any error messages
            password2.setCustomValidity('');
            passwordError.textContent = '';
            passwordError.style.display = 'none';
        }
    }
    
    // Event listeners for input on both password fields
    password1.addEventListener('input', function() {
        validatePasswordStrength();
        updateErrorMessage();
    });
    
    password2.addEventListener('input', updateErrorMessage);
}
    
    // Toggle visibilkity on users profile books

    document.querySelectorAll('.toggle-visibility').forEach(function(button) {
        // Set initial text and class based on the current state
        button.textContent = button.getAttribute('data-current-state') === 'true' ? 'Display on Profile' : 'Hide From Profile';
        button.classList.toggle('btn-primary', button.getAttribute('data-current-state') !== 'true');
        button.classList.toggle('btn-danger', button.getAttribute('data-current-state') === 'true');
    
        button.addEventListener('click', function() {
            let bookId = this.getAttribute('data-book-id');
            
            // Current state inside the click event listener
            let currentState = this.getAttribute('data-current-state') === 'true';
    
            // Determine the intended new state (opposite of current)
            let newState = !currentState;
    
            // Update text and class to reflect the intended new state
            this.textContent = newState ? 'Hide From Profile' : 'Display on Profile';
            this.classList.toggle('btn-primary', newState);
            this.classList.toggle('btn-danger', !newState);
    
            fetch(`/books/toggle_visibility/${bookId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    // Revert text and class if the server update fails
                    newState = currentState; // Revert newState to the original currentState
                } else {
                    // Update currentState to reflect the successful change
                    currentState = newState;
                }
                this.setAttribute('data-current-state', currentState.toString());
                this.textContent = currentState ? 'Display on Profile' : 'Hide From Profile';
                this.classList.toggle('btn-primary', !currentState);
                this.classList.toggle('btn-danger', currentState);
            })
            .catch(error => {
                console.error('Error:', error);
                // Revert text and class in case of an error
                newState = currentState; // Revert newState to the original currentState
                this.setAttribute('data-current-state', currentState.toString());
                this.textContent = currentState ? 'Display on Profile' : 'Hide From Profile';
                this.classList.toggle('btn-primary', !currentState);
                this.classList.toggle('btn-danger', currentState);
            });
        });
    });
    


        // getCookie function remains the same
        

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                let cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    let cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

});

document.addEventListener('DOMContentLoaded', function() {

    //Quick Notes Update
    const form = document.getElementById('quick-notes-form');
    const notesList = document.getElementById('quick-notes-list');

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(this);

        fetch('/add_quick_note/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken 
            }
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Create new note element and add it to the list
                const newNote = document.createElement('div');
                newNote.className = 'quick-note';
                newNote.innerHTML = `
                    <p>${data.note}</p>
                    <span class="timestamp">${data.created_at}</span>
                `;
                notesList.prepend(newNote); // Add the new note at the beginning of the list
            } else {
            }
        })
        .catch(error => console.error('Error:', error));
    });

});


window.onload = function() {

    // Modal setup
    var modal = document.getElementById("demoModal");
    var span = document.getElementsByClassName("close")[0];

    // Display the modal by default
    modal.style.display = "block";

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
        modal.style.display = "none";
    };

    // Close modal if the user clicks anywhere outside of it
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };
};
