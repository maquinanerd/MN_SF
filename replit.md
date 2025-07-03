# Content Automation System

## Overview

The Content Automation System is a Flask-based web application that automates the collection, processing, and publishing of entertainment articles from RSS feeds. The system uses Google Gemini AI to translate and rewrite content from ComicBook.com feeds, then automatically publishes the processed articles to a WordPress website (maquinanerd.com.br). The system handles movies and TV shows content with specialized AI prompts for each category.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: PostgreSQL for data persistence with connection pooling
- **Scheduling**: APScheduler for automated task execution every 15 minutes
- **AI Processing**: Google Gemini AI with multiple API keys for redundancy
- **Content Management**: WordPress REST API integration for automated publishing

### Frontend Architecture
- **UI Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JS for dashboard interactions and real-time updates
- **Templating**: Jinja2 templates with base template inheritance

## Key Components

### Core Application (`app.py`)
- Flask application factory with SQLAlchemy integration
- Database configuration with pool recycling and pre-ping health checks
- Blueprint-based modular routing system
- Proxy fix middleware for deployment environments

### Data Models (`models.py`)
- **Article**: Main entity storing original content, processed content, WordPress data, and status tracking
- **ProcessingLog**: Audit trail for all processing activities and error tracking
- Comprehensive status workflow: pending → processing → processed → published

### Services Layer
- **RSS Monitor**: Fetches new articles from ComicBook.com movie and TV show feeds using feedparser and trafilatura
- **AI Processor**: Singleton pattern processor with specialized prompts for cinema vs series content
- **WordPress Publisher**: Handles article publishing, image uploads, and category/tag management
- **Scheduler**: Background automation orchestrating the entire workflow

### Configuration Management (`config.py`)
- RSS feed endpoints for movies and TV shows
- Multiple Gemini AI API keys with primary/backup configuration
- WordPress authentication and category mapping
- Universal prompt template for content processing

## Data Flow

1. **Content Collection**: RSS Monitor fetches new articles every 15 minutes from specified feeds
2. **Content Extraction**: Full article content extracted using trafilatura with featured image detection
3. **AI Processing**: Articles processed by appropriate AI (cinema for movies, series for TV shows) using universal prompt
4. **Content Publishing**: Processed articles published to WordPress with SEO optimization, categories, and tags
5. **Status Tracking**: Complete audit trail maintained throughout the entire process

## External Dependencies

### Third-Party Services
- **Google Gemini AI**: Content translation and rewriting with JSON response format
- **WordPress REST API**: Automated publishing to maquinanerd.com.br
- **ComicBook.com RSS**: Source feeds for entertainment content

### Python Libraries
- Flask ecosystem (Flask, SQLAlchemy, Jinja2)
- feedparser for RSS feed parsing
- trafilatura for content extraction
- APScheduler for background task automation
- requests for HTTP communications
- BeautifulSoup for HTML parsing

## Deployment Strategy

### Environment Configuration
- PostgreSQL database connection via DATABASE_URL environment variable
- Multiple Gemini API keys for redundancy and rate limiting
- WordPress credentials stored in environment variables
- Session secret for Flask security

### Monitoring and Logging
- Comprehensive logging throughout all components
- Real-time dashboard with status monitoring
- Processing time tracking and error handling
- Automatic retry mechanisms for failed operations

## Changelog
- July 03, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.