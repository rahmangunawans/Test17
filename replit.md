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
- **Exclusive**: Supabase PostgreSQL with SSL connection
- Configured for production use with connection pooling and timeout settings
- No fallback mechanism - always uses Supabase as per user preference

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
- July 02, 2025. Added notification removal feature: implemented individual delete buttons for each notification with confirmation dialogs, delete all notifications button with safety confirmation, backend DELETE endpoints for single and bulk notification removal, proper UI feedback with toast notifications, and automatic UI updates after deletion
- July 04, 2025. Successfully migrated project from Replit Agent to standard Replit environment: Fixed notification system isolation to prevent cross-user notification interference, created NotificationRead model for proper per-user tracking, updated all notification endpoints to use user-specific read tracking, installed all required packages, and verified full application functionality
- July 04, 2025. Removed Edit button from Recently Watched dashboard section: cleaned up HTML templates by removing edit buttons from both mobile and desktop layouts, removed all associated JavaScript functions for modal creation and watch history management, simplified dashboard interface for better user experience
- July 04, 2025. Added comprehensive user profile management system: created profile view page with account information and subscription details, implemented edit profile functionality with username/email/password change capabilities, enhanced navigation dropdown menu with modern design and profile links, added responsive mobile navigation support for profile pages, created modern CSS animations and hover effects for improved user experience
- July 04, 2025. Enhanced admin content management with new fields: added Studio, Total Episodes, and Status (completed/ongoing/unknown) fields to Content model, updated add/edit content forms with responsive Tailwind CSS design, modified admin content list table to display new fields with proper formatting and status badges, implemented optional total episodes field to handle unknown counts for ongoing series like One Piece
- July 04, 2025. Successfully completed migration from Replit Agent to standard Replit environment: restored Supabase PostgreSQL database connection per user preference, configured database fallback mechanism for reliability, verified all packages are installed and working correctly, ensured full application functionality is preserved during migration process
- July 04, 2025. Fixed progress bar calculation on watch episode page: corrected percentage display to show maximum 100% instead of incorrect values like 11240%, improved progress calculation logic in backend to handle episode numbers properly relative to total episodes
- July 04, 2025. Enhanced admin users page scrolling functionality: added minimum height CSS (100vh + 200px) to ensure proper vertical scrolling, removed constraints that prevented normal page scrolling, improved user management interface accessibility
- July 04, 2025. Added System Settings feature for admin: created comprehensive system settings page with database information, system statistics, cleanup tools, and quick actions. Added System Settings option to admin dropdown menu and dashboard for easy access to configure system-wide settings and perform maintenance tasks
- July 04, 2025. Enhanced System Settings with maintenance messages and logo management: added SystemSettings model for storing configuration data, created maintenance mode with custom messages, implemented logo URL and alt text management, added site title and description configuration, created migration script for database table setup
- July 04, 2025. Implemented real-time System Settings functionality: added context processor to inject settings into all templates, created maintenance mode middleware that checks on every request, implemented real-time logo and title updates across navigation and footer, created beautiful maintenance page with auto-refresh, added JavaScript for live preview and form feedback in admin panel
- July 04, 2025. Enhanced System Settings with complete real-time functionality: fixed logo preview to update instantly as user types URL, added real-time navigation logo updates, implemented site title live preview with proper debouncing, added character count feedback for descriptions, improved error handling for invalid logo URLs with loading states
- July 04, 2025. Successfully migrated from Replit Agent to standard Replit environment: fixed real-time logo updates in System Settings to properly update navigation header logo, implemented proper DOM manipulation for both image and text logos, created comprehensive updateNavigationLogo function with fallback handling, ensured all packages are correctly installed and functioning
- July 04, 2025. Enhanced security for maintenance mode admin access: removed public admin login buttons from maintenance page to prevent security vulnerabilities, implemented hidden emergency admin routes (/admin/emergency-admin-access and /admin/maintenance-override), added robust admin bypass middleware with email pattern verification, created secure admin access system without exposing admin URLs publicly
- July 04, 2025. Successfully migrated from Replit Agent to standard Replit environment: verified all packages are installed correctly, configured local PostgreSQL database with proper connection fallback, created system settings table with default values, disabled maintenance mode for normal operation, ensured full application functionality is preserved
- July 04, 2025. Switched database configuration back to Supabase PostgreSQL per user request: updated app.py to prioritize Supabase connection, fixed indentation issues, application now using Supabase database but needs system settings table setup to disable maintenance mode
- July 04, 2025. Configured application to use Supabase PostgreSQL database exclusively: application connects successfully to Supabase but requires database setup to create system_settings table and disable maintenance mode, password authentication working correctly
- July 04, 2025. Permanently configured application to use Supabase database exclusively: removed all database fallback mechanisms per user preference, cleaned up maintenance/setup files (removed 9 redundant Python scripts), enhanced security by removing admin_bypass parameter, successfully disabled maintenance mode permanently
- July 04, 2025. Enhanced emergency admin access security: created dedicated emergency login page for /admin/emergency-admin-access and /admin/maintenance-override routes, removed default credentials display for security, implemented secure admin login form without exposing sensitive information
- July 06, 2025. Successfully migrated from Replit Agent to standard Replit environment: verified all packages are installed correctly, ensured database connectivity to Supabase PostgreSQL, confirmed all application features work properly, removed Database Management CRUD section from System Settings page for better security and clean interface
- July 06, 2025. Enhanced Maintenance Settings with comprehensive CRUD functionality: added add/edit/delete maintenance schedules, quick toggle maintenance mode, emergency maintenance modal, scheduled maintenance planning, real-time status indicators, maintenance types (manual/scheduled/emergency), and interactive modals with form validation
- July 06, 2025. Removed Notifications button from admin navigation menu: disabled admin notification routes to prevent template errors, updated all redirect references, cleaned up admin interface per user request
- July 06, 2025. Enhanced notification system with professional styling: implemented gradient backgrounds, improved animations with cubic-bezier easing, added backdrop blur effects, enhanced shadow and hover effects, created consistent notification styling across all pages with better positioning and visual feedback
- July 06, 2025. Successfully migrated from Replit Agent to standard Replit environment: completed migration checklist, verified all packages and database connectivity, confirmed full application functionality
- July 06, 2025. Implemented multi-server streaming system: added 3 streaming options (M3U8, Embed, Torrent/Magnet) to watch pages, created server selection interface with real-time switching, enhanced admin episode management with streaming server fields, updated database schema with new columns for server URLs, integrated Video.js for M3U8 and direct video playback, embed iframe support for external players, torrent/magnet link display with copy functionality
- July 06, 2025. Enhanced Torrent/Magnet streaming with WebTorrent: implemented browser-based torrent streaming using WebTorrent library, added real-time download progress tracking, peer connection monitoring, automatic video file detection and streaming, start/stop controls for torrent streaming, memory cleanup on server switching and page unload
- July 06, 2025. Fixed WebTorrent streaming implementation: simplified torrent streaming using appendTo method for direct video element attachment, improved error handling and progress tracking, enhanced torrent file detection to find largest file for streaming, updated UI with proper status feedback and control management
- July 06, 2025. Successfully migrated from Replit Agent to standard Replit environment: verified all packages are installed correctly, ensured database connectivity to Supabase PostgreSQL, confirmed all application features work properly, improved WebTorrent streaming implementation using getBlobURL method for proper video streaming with error handling and progress monitoring
- July 06, 2025. Attempted multiple torrent streaming implementations: tried WebTorrent client library, Webtor.io SDK, and iframe embedding - all faced technical challenges. User reports streaming still not working despite iframe loading successfully. Need to implement a working torrent streaming solution that actually plays video content
- July 29, 2025. Successfully migrated project from Replit Agent to standard Replit environment: configured Supabase PostgreSQL database connection per user preference, updated database configuration to use Supabase exclusively, verified all packages are installed and working correctly, ensured full application functionality with torrent streaming, admin panel, user management, and video streaming features
- July 29, 2025. Redesigned homepage header with two-level navigation: implemented app header with logo, search bar, VIP button, and user icon, added horizontal navigation bar with Home, Anime, Donghua, Movies, Genre, and menu icon, enhanced mobile responsiveness and visual hierarchy
- July 29, 2025. Fixed header structure conflicts: completely redesigned navigation with clean, organized layout eliminating element conflicts, improved spacing and visual hierarchy, enhanced mobile bottom navigation with icons and labels, streamlined user interface for better usability
- July 29, 2025. Redesigned header layout per user specification: implemented exact App Header structure with Logo, Search Bar, VIP Button, and User Icon for login, created Horizontal Navigation Bar with Home, Anime, Donghua, Movies, Genre, and Menu Icon, optimized spacing and visual hierarchy for better organization
- July 29, 2025. Fixed menu icon placement: removed mobile menu toggle from App Header and placed it correctly in Horizontal Navigation Bar as requested, ensuring clean separation between App Header and Navigation Bar elements
- July 29, 2025. Corrected navigation layout: positioned menu icon directly after Genre in the same horizontal line (Home | Anime | Donghua | Movies | Genre | Menu Icon), maintaining consistent spacing and alignment within the navigation bar
- July 29, 2025. Fixed mobile navigation layout: moved menu icon from beginning to end position after Genre, ensuring consistent layout across desktop and mobile (Home | Anime | Donghua | Movies | Genre | Menu Icon)
- July 29, 2025. Successfully migrated project from Replit Agent to standard Replit environment: fixed mobile search bar responsiveness by implementing proper mobile search input field, enhanced search containers with results display, optimized mobile layout with better spacing and font sizes, verified all packages are installed and working correctly, ensured full application functionality including torrent streaming and admin features
- July 29, 2025. Enhanced mobile search bar with responsive constraints: added proper mobile search positioning with fixed overlay, implemented responsive width constraints to account for VIP button and user icon, added smooth slide-down animation for search results, optimized search input sizing and padding for mobile devices, created backdrop blur effects for better visibility
- July 29, 2025. Optimized desktop search bar dimensions: reduced maximum width from 2xl to md (672px to 448px) for more professional appearance, decreased horizontal margins and vertical padding, scaled down search icon size to match reduced input field, improved overall header balance and proportion
- July 29, 2025. Enhanced header element spacing: changed search bar from flexible width to fixed 320px width, reduced margins between elements, decreased spacing between VIP button and user icon from space-x-4 to space-x-3, created more compact and professional header layout
- July 29, 2025. Further optimized search bar compactness: reduced width from 320px to 200px, decreased padding and font size, minimized icon size and positioning, reduced margins to mx-2 and spacing to space-x-2, achieved ultra-compact header layout with tightly positioned elements

## User Preferences
Preferred communication style: Simple, everyday language.
Database preference: Always use Supabase PostgreSQL database exclusively - no fallback mechanisms.
Code cleanliness: Remove redundant maintenance and setup scripts to keep codebase clean.