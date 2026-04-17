# Farmer-Hub System Specification

## 1. Project Overview

**Project Name:** Farmer-Hub  
**Project Type:** Full-stack Web Application  
**Core Functionality:** A comprehensive platform where farmers can buy/sell seeds and animals, interact with other farms for bargaining and knowledge sharing, post questions, and get help from the community.  
**Target Users:** Farmers, agricultural businesses, and agricultural enthusiasts

## 2. Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Backend:** Python with Flask framework
- **Database:** SQLite (SQLAlchemy ORM)
- **Authentication:** Session-based with social login simulation

## 3. UI/UX Specification

### Layout Structure

**Pages:**
1. Splash Screen (animated loading)
2. Login Page
3. Signup Page (with social signup options)
4. Dashboard/Home Page
5. Marketplace (Seeds & Animals)
6. Community Forum
7. Profile Page

### Visual Design

**Color Palette:**
- Primary: `#2D5A27` (Forest Green)
- Secondary: `#8B4513` (Saddle Brown)
- Accent: `#FFD700` (Gold)
- Background: `#F5F5DC` (Beige)
- Text Primary: `#1A1A1A`
- Text Secondary: `#4A4A4A`
- Success: `#28A745`
- Error: `#DC3545`
- Card Background: `#FFFFFF`

**Typography:**
- Headings: 'Playfair Display', serif
- Body: 'Source Sans Pro', sans-serif
- Font Sizes:
  - H1: 2.5rem
  - H2: 2rem
  - H3: 1.5rem
  - Body: 1rem
  - Small: 0.875rem

**Spacing:**
- Base unit: 8px
- Margins: 8px, 16px, 24px, 32px, 48px
- Paddings: 8px, 16px, 24px, 32px
- Border Radius: 8px (cards), 4px (buttons), 50% (avatars)

**Visual Effects:**
- Box shadows: `0 4px 6px rgba(0,0,0,0.1)`
- Hover transitions: 0.3s ease
- Gradient backgrounds for hero sections
- Smooth page transitions

### Components

**Navigation Bar:**
- Logo (left)
- Navigation links (center)
- User profile dropdown (right)
- Responsive hamburger menu

**Cards:**
- Product cards with image, title, price, seller info
- Question cards with title, author, date, reply count
- User cards with avatar, name, location

**Buttons:**
- Primary: Green background, white text
- Secondary: Brown background, white text
- Outline: Transparent with border
- States: hover, active, disabled

**Forms:**
- Floating labels
- Input validation
- Error/success messages
- Loading states

## 4. Functionality Specification

### Splash Screen
- Animated logo with farming-themed icon
- Progress indicator
- Auto-redirect to login after 3 seconds

### Authentication
- **Login:** Email/password
- **Signup:** Name, email, password, confirm password, location, farm type
- **Social Signup:** Google, Facebook, Twitter (simulated)
- Session management
- Logout functionality

### Dashboard
- Welcome message with user name
- Quick stats (products listed, questions asked, connections)
- Recent activity feed
- Quick action buttons

### Marketplace
- **Categories:**
  - Seeds (vegetables, fruits, grains, flowers)
  - Animals (livestock, poultry, aquaculture)
- **Features:**
  - Browse by category
  - Search functionality
  - Product details (image, description, price, quantity, seller)
  - Add to cart
  - Contact seller (bargaining)
  - Filter by price, location, rating

### Community Forum
- **Post Questions:**
  - Title, description, category
  - Attach images
  - Tag topics
- **Reply to Questions:**
  - Text replies
  - Upvote helpful answers
  - Mark as solution
- **Categories:** Crop Farming, Animal Husbandry, Equipment, Weather, Market Prices

### User Profile
- Edit profile information
- View listings
- View questions asked
- Settings (notifications, privacy)

### Bargaining System
- Send offer to seller
- Counter-offer functionality
- Accept/reject offers
- Message history

## 5. Database Schema

### Users Table
- id, username, email, password_hash, full_name, location, farm_type, bio, avatar, created_at

### Products Table
- id, seller_id, title, description, category, subcategory, price, quantity, unit, image_url, status, created_at

### Questions Table
- id, author_id, title, description, category, tags, image_url, solved, created_at

### Answers Table
- id, question_id, author_id, content, upvotes, is_solution, created_at

### Offers Table
- id, product_id, buyer_id, seller_id, offer_price, status, message, created_at

### Messages Table
- id, sender_id, receiver_id, content, read, created_at

## 6. File Structure

```
farmer-hub/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── instance/                 # SQLite database
├── static/
│   ├── css/
│   │   ├── style.css        # Main styles
│   │   ├── components.css   # Component styles
│   │   └── animations.css   # Animations
│   ├── js/
│   │   ├── main.js          # Main JavaScript
│   │   ├── auth.js          # Authentication
│   │   ├── marketplace.js   # Marketplace logic
│   │   └── forum.js         # Forum logic
│   └── images/              # Static images
└── templates/
    ├── splash.html          # Splash screen
    ├── login.html            # Login page
    ├── signup.html           # Signup page
    ├── dashboard.html       # User dashboard
    ├── marketplace.html      # Marketplace
    ├── product.html         # Product details
    ├── forum.html           # Community forum
    ├── question.html        # Question details
    ├── profile.html         # User profile
    └── layout.html          # Base layout template
```

## 7. Acceptance Criteria

### Visual Checkpoints
- [ ] Splash screen displays with animation
- [ ] Login/Signup pages are properly styled
- [ ] Dashboard shows user information
- [ ] Marketplace displays products in grid
- [ ] Forum shows questions list
- [ ] Navigation works across all pages
- [ ] Responsive design works on mobile

### Functional Checkpoints
- [ ] User can sign up with email
- [ ] User can log in
- [ ] User can browse products
- [ ] User can post a question
- [ ] User can reply to questions
- [ ] User can create product listings
- [ ] Bargaining system works
- [ ] Data persists in database
