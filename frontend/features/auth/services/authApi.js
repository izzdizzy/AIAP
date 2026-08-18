import apiClient from '../../../services/apiClient';

export function register(name, email, password) {
  return apiClient('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password })
  });
}

export function login(email, password) {
  return apiClient('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export function fetchMe() {
  return apiClient('/auth/me');
}

export function changePassword(currentPassword, newPassword) {
  return apiClient('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
  });
}
