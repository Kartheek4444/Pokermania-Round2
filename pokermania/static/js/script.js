function changePage(page) {
    // Hide all pages first
    const pages = ['home', 'play', 'leaderboard'];
    pages.forEach(p => {
        const element = document.getElementById(`${p}-page`);
        if (element) {
            element.style.display = 'none';
        }
    });
    
    // Show the selected page
    const selectedPage = document.getElementById(`${page}-page`);
    if (selectedPage) {
        selectedPage.style.display = 'block';
    }
    
    // If it's the home page, redirect to index.html
    if (page === 'home') {
        window.location.href = 'index.html';
    }
}

// Bot deployment handling
function handleBotSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const botName = form.querySelector('#botName').value;
    const botFile = form.querySelector('#botFile').files[0];
    const description = form.querySelector('#description').value;

    // Show deployment status
    const deploymentStatus = document.querySelector('.deployment-status');
    const statusMessage = document.querySelector('#statusMessage');
    const progressBar = document.querySelector('.progress');
    
    deploymentStatus.style.display = 'block';
    statusMessage.textContent = 'Uploading bot...';
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += 10;
        progressBar.style.width = `${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
            statusMessage.textContent = 'Bot deployed successfully!';
            
            // Reset form after successful deployment
            setTimeout(() => {
                form.reset();
                deploymentStatus.style.display = 'none';
                progressBar.style.width = '0%';
            }, 2000);
        }
    }, 300);

    // In a real application, you would send the data to your server here
    console.log('Bot Details:', {
        name: botName,
        file: botFile,
        description: description
    });
}


// File validation
document.getElementById('botFile')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file && !file.name.endsWith('.py')) {
        alert('Please upload a Python (.py) file only');
        e.target.value = '';
    }
});


//  // Password strength validation
// document.getElementById('signupPassword').addEventListener('input', function() {
//     let password = this.value;
//     let message = '';

//     // Check password length
//     if (password.length < 8) {
//         message += 'Password must be at least 8 characters long.\n';
//     }
//     // Check if password contains a number
//     if (!/\d/.test(password)) {
//         message += 'Password must contain at least one number.\n';
//     }
//     // Check if password contains a special character
//     if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
//         message += 'Password must contain at least one special character.\n';
//     }
//     // Check if password contains an uppercase letter
//     if (!/[A-Z]/.test(password)) {
//         message += 'Password must contain at least one uppercase letter.\n';
//     }

//     // Display password strength message
//     document.getElementById('passwordMessage').textContent = message;

//     // Clear message if password is valid
//     if (message === '') {
//         document.getElementById('passwordMessage').textContent = '';
//     }

//     // Recheck password match when password is changed
//     checkPasswordMatch();
// });

// // Password match validation
// document.getElementById('confirmPassword').addEventListener('input', function() {
//     checkPasswordMatch();
// });

// function checkPasswordMatch() {
//     let password = document.getElementById('signupPassword').value;
//     let confirmPassword = document.getElementById('confirmPassword').value;
//     let matchMessage = '';

//     // Only perform the check if both fields have content
//     if (password && confirmPassword) {
//         if (password !== confirmPassword) {
//             matchMessage = 'Passwords do not match!';
//             document.getElementById('passwordMatchMessage').style.color = 'red';
//         } else {
//             matchMessage = 'Passwords match!';
//             document.getElementById('passwordMatchMessage').style.color = 'green';
//         }
//     } else {
//         matchMessage = ''; // Clear the message if either field is empty
//     }

//     // Display password match message
//     document.getElementById('passwordMatchMessage').textContent = matchMessage;
// }
