document.addEventListener('DOMContentLoaded', function() {
  const password = document.getElementById('password');
  const confirmPassword = document.getElementById('confirm_password');
  const strengthMeter = document.getElementById('password-strength');
  const matchStatus = document.getElementById('password-match');

  function checkPasswordStrength(password) {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    const isLongEnough = password.length >= 8;
    
    const strength = [hasUpperCase, hasLowerCase, hasNumbers, hasSpecialChar, isLongEnough]
      .filter(Boolean).length;
    
    strengthMeter.className = 'strength-meter';
    if (strength < 2) strengthMeter.classList.add('weak');
    else if (strength < 4) strengthMeter.classList.add('medium');
    else strengthMeter.classList.add('strong');
  }

  function checkPasswordMatch() {
    matchStatus.className = 'match-status';
    if (password.value && confirmPassword.value) {
      if (password.value === confirmPassword.value) {
        matchStatus.textContent = '✓ Passwords match';
        matchStatus.classList.add('match');
      } else {
        matchStatus.textContent = '× Passwords do not match';
        matchStatus.classList.add('no-match');
      }
    }
  }

  password.addEventListener('input', () => {
    checkPasswordStrength(password.value);
    checkPasswordMatch();
  });

  confirmPassword.addEventListener('input', checkPasswordMatch);
});