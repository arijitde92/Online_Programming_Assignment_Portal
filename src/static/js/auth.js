// Prevent back button after logout
window.addEventListener('load', function() {
    // Function to check if user is logged in
    function isLoggedIn() {
        return document.cookie.includes('session=') || document.cookie.includes('remember_token=');
    }

    // Function to handle back button
    function handleBackButton(e) {
        if (!isLoggedIn()) {
            // If user is not logged in, prevent going back
            window.history.pushState(null, '', window.location.href);
            window.location.href = '/';  // Redirect to index page
        }
    }

    // Add event listener for popstate (back/forward button)
    window.addEventListener('popstate', handleBackButton);

    // Clear browser history and add current page
    window.history.pushState(null, '', window.location.href);

    // Add event listener for beforeunload
    window.addEventListener('beforeunload', function(e) {
        if (!isLoggedIn()) {
            // Clear any stored data
            localStorage.clear();
            sessionStorage.clear();
        }
    });
}); 