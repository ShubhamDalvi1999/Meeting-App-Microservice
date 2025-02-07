# Installation Guide

## Prerequisites

1. **Required Software**
   - Node.js (v18 or higher)
   - Python (v3.9 or higher)
   - PostgreSQL (v14 or higher)
   - Git

2. **Development Tools**
   - Visual Studio Code (recommended)
   - PostgreSQL client (e.g., pgAdmin)
   - Postman (for API testing)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/meeting-management-system.git
cd meeting-management-system
```

### 2. Backend Setup

1. Create Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and other settings
   ```

4. Initialize database:
   ```bash
   flask db upgrade
   flask seed  # If seed command is available
   ```

### 3. Frontend Setup

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API endpoints and other settings
   ```

### 4. Database Setup

1. Create PostgreSQL database:
   ```sql
   CREATE DATABASE meeting_management;
   ```

2. Grant privileges to your user:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE meeting_management TO your_user;
   ```

## Running the Application

1. Start the backend server:
   ```bash
   # In the backend directory
   flask run
   ```

2. Start the frontend development server:
   ```bash
   # In the frontend directory
   npm run dev
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in .env
   - Ensure database exists and user has proper permissions

2. **Node.js Dependencies**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

3. **Python Dependencies**
   - Ensure virtual environment is activated
   - Update pip: `python -m pip install --upgrade pip`
   - Install wheel package: `pip install wheel`

### Getting Help

- Check the project's issue tracker
- Review the documentation in the `docs` directory
- Contact the development team

## Next Steps

After installation:
1. Review the [Quick Start Guide](./quick-start.md)
2. Familiarize yourself with [Common Commands](./commands.md)
3. Set up your [Local Development Environment](./local-development.md) 