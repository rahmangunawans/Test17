# AniFlix - Anime and Movie Streaming Platform

## Overview
AniFlix is a premium anime and movie streaming platform built with Flask. The application provides a Netflix-like experience for anime content with features including user authentication, subscription management, video streaming, and admin controls. It supports both free and VIP subscription tiers with content access restrictions based on user status.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLalchemy ORM
- **Database**: PostgreSQL (Supabase) with fallback to Replit Database
- **Authentication**: Flask-Login with session-based authentication
- **Payment Processing**: Stripe integration for subscription management

### Frontend Architecture
- **Templating**: Jinja2 templates with responsive design
- **Styling**: Tailwind CSS for modern UI components
- **JavaScript**: Vanilla JS for interactive features
- **Video Player**: Video.js for streaming functionality

## Key Components

### User Management System
- User registration and authentication with email/password
- Role-based access control (regular users vs admin)
- Admin users identified by email patterns (@admin.aniflix.com, admin@*, or containing 'admin')
- Session management with Flask-Login

### Subscription System
- **Free Tier**: Access to first 5 episodes, 10-minute preview for episodes 6+
- **VIP Tiers**: 
  - Monthly ($3.00)
  - 3-Month ($8.00) 
  - Yearly ($28.00)
- Stripe integration for payment processing
- Automatic access control based on subscription status

### Content Management
- Support for both anime series and movies
- Episode-based content organization
- Genre categorization and filtering
- Admin interface for content and episode management
- Thumbnail and video URL management

### Video Streaming
- Video.js player integration
- Progress tracking and resume functionality
- Quality controls and playback rate adjustment
- Content restrictions based on user subscription

### Admin Panel
- Dashboard with platform statistics
- User management with subscription control
- Content and episode management
- Analytics and viewing statistics

## Data Flow

### User Authentication Flow
1. User submits login credentials
2. Server validates against database
3. Flask-Login creates session
4. User role and subscription status determined
5. Content access permissions calculated

### Content Access Flow
1. User requests content/episode
2. System checks subscription status and expiration
3. Access permissions calculated based on episode number and user tier
4. Content served with appropriate restrictions
5. Watch progress tracked and stored

### Admin Operations Flow
1. Admin authentication via email pattern matching
2. Admin-only routes protected by decorator
3. CRUD operations on users, content, and episodes
4. Real-time statistics calculation and display

## External Dependencies

### Payment Processing
- **Stripe**: Subscription payment processing
- Environment variables for API keys and price IDs
- Webhook handling for subscription events

### Database
- **Primary**: Supabase PostgreSQL with SSL connection
- **Fallback**: Replit Database via DATABASE_URL
- Connection pooling and timeout configuration

### CDN and Assets
- **Tailwind CSS**: Via CDN for styling
- **Font Awesome**: Icon library
- **Google Fonts**: Poppins font family
- **Video.js**: Video player library

### Email Services
- Admin identification via email pattern matching
- Future email notification capabilities

## Deployment Strategy

### Environment Configuration
- Development and production environment support
- Environment variables for database connections, API keys, and secrets
- SSL/TLS configuration for database connections
- Proxy fix middleware for deployment behind reverse proxies

### Database Configuration
- Automatic connection fallback mechanism
- Connection pooling with health checks
- SSL requirement for production database connections
- Migration support through SQLAlchemy

### Static Asset Management
- CSS and JavaScript file organization
- CDN integration for external libraries
- Responsive design optimization
- Custom scrollbar and UI enhancements

## Changelog
- July 02, 2025. Initial setup
- July 02, 2025. Fixed analytics page template consistency - changed from admin/base.html to responsive_base.html to match other admin pages
- July 02, 2025. Fixed navigation conflict on all admin pages - changed py-8 to pt-24 pb-8 to avoid header overlap with main navigation
- July 02, 2025. Fixed scrolling issues on admin content management pages - removed min-h-screen constraint, added proper overflow CSS properties to enable vertical scrolling
- July 02, 2025. Added search functionality to admin content and episodes pages with responsive design, tooltip support for mobile, and enhanced action buttons with hover effects
- July 02, 2025. Enhanced admin interface with comprehensive animations including card hover effects, button ripple effects, table row animations, search input scaling, and gradient backgrounds for better visual appeal
- July 02, 2025. Migrated project from Replit Agent to standard Replit environment with improved security and compatibility
- July 02, 2025. Optimized search performance: single database query with ranking, client-side caching (30s), request throttling (300ms), and increased debounce delay (500ms) to reduce server load and improve response times
- July 02, 2025. Added comprehensive real-time notification system with Socket.IO: notification bell in nav, real-time push notifications, admin notification management panel, automatic subscription success notifications, and toast notifications with action URLs
- July 02, 2025. Fixed "add episode" functionality by adding missing thumbnail_url column to Episode model and optimized performance by replacing Socket.IO with lightweight polling to eliminate worker timeouts
- July 02, 2025. Successfully migrated from Replit Agent to standard Replit environment: configured local PostgreSQL database, updated database connection logic to prioritize Replit's DATABASE_URL, ensured all dependencies work correctly, and verified full application functionality
- July 02, 2025. Added Trailer URL field to Add Content form with full backend integration for content management
- July 02, 2025. Implemented real-time notifications with Socket.IO: replaced polling with WebSocket connections, added Socket.IO client library, configured real-time event emission for new content/episodes, and verified successful connection with instant notification delivery
- July 02, 2025. Optimized notification system: reduced polling frequency from 5 seconds to 60 seconds to minimize server load, fixed "mark all as read" functionality with user feedback, and implemented automatic deletion of notifications older than 5 days to keep database clean
- July 02, 2025. Completely removed automatic notification polling: notifications now only load on page load/login or manual refresh to eliminate unnecessary server requests, added manual refresh button with loading animation and feedback, implemented smart refresh when user returns after 5+ minutes away
- July 02, 2025. Fixed read_at implementation: properly display read timestamp in notifications, improved datetime handling with timezone support for Indonesia, enhanced notification UI to show when notifications were read, eliminated all automatic polling for better performance
- July 02, 2025. Complete notification system rewrite: created new manual-only notification system with no automatic polling, proper read_at timestamp display showing both creation and read times, enhanced UI with visual indicators for read/unread status, manual refresh button with feedback, and robust error handling for better user experience

## User Preferences
Preferred communication style: Simple, everyday language.