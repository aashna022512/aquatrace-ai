# Firebase Authentication Integration Plan

## Backend Changes
- [x] Update backend/app.py to integrate Firebase Admin SDK for token verification
- [x] Add Firebase ID token verification endpoint
- [x] Modify login flow to accept Firebase ID tokens
- [x] Update User model to use firebase_uid for authentication
- [ ] Remove/disable existing Google and GitHub OAuth routes
- [ ] Update session management for Firebase auth

## Frontend Changes
- [x] Update backend/templates/login.html to use Firebase client SDK
- [x] Add Firebase configuration and initialization
- [x] Implement Firebase authentication UI (login/register)
- [ ] Update backend/templates/register.html if needed
- [ ] Modify login form to send Firebase ID token to backend

## Configuration
- [ ] Add Firebase project configuration to .env
- [ ] Update requirements.txt if needed
- [ ] Test Firebase authentication flow

## Testing
- [ ] Test login with Firebase Authentication
- [ ] Test user registration via Firebase
- [ ] Verify session management works
- [ ] Test logout functionality

# Mobile Layout Fixes for index.html

## Tasks
- [ ] Add comprehensive mobile media queries to backend/templates/index.html inline styles
- [ ] Enhance mobile responsiveness in backend/static/style/style.css
- [ ] Ensure all sections (hero, features, stats, conservation, technology, CTA) display properly on mobile
- [ ] Adjust grid layouts to stack vertically on mobile screens
- [ ] Optimize font sizes, padding, and margins for mobile devices
- [ ] Make buttons and interactive elements touch-friendly
- [ ] Test layout on mobile devices/simulator

# Mobile Layout Fixes for about.html

## Tasks
- [x] Adjust paddings in .mission-content and .mission-text for mobile to maximize text width
- [x] Add word-breaking CSS (word-wrap: break-word; hyphens: auto;) to .mission-text on mobile
- [x] Ensure .mission-image img scales responsively on mobile (max-width:100%; height:auto;)
- [x] Add specific rules for smaller screens (max-width:480px) to fine-tune font-size and line-height
- [ ] Test the updated layout on mobile to verify text flows better without awkward wrapping
