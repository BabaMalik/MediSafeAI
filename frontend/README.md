# MediSafeAI Frontend

React-based web interface for the MediSafeAI synthetic healthcare data generator.

## Features

- **User Authentication**: JWT-based login and registration
- **Dashboard**: System status and quick access to features
- **Data Generation**: Generate synthetic patient, vitals, and treatment data
- **Privacy Management**: Apply differential privacy and track budget usage
- **Responsive Design**: Material-UI components for modern, clean UI

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- MediSafeAI backend running on http://localhost:5000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

### Production Build

```bash
npm run build
```

Builds the app for production to the `build` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/      # Reusable UI components
│   │   └── Layout.js    # Main layout with navigation
│   ├── contexts/        # React contexts
│   │   └── AuthContext.js
│   ├── pages/           # Page components
│   │   ├── Dashboard.js
│   │   ├── DataGeneration.js
│   │   ├── Login.js
│   │   ├── PrivacyManagement.js
│   │   └── Register.js
│   ├── services/        # API services
│   │   └── api.js
│   ├── App.js          # Main app component
│   └── index.js        # Entry point
├── package.json
└── README.md
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:5000
```

## Available Routes

- `/login` - User login
- `/register` - User registration
- `/dashboard` - Main dashboard (protected)
- `/generate` - Data generation interface (protected)
- `/privacy` - Privacy management (protected)

## Authentication

The frontend uses JWT tokens stored in localStorage:
- `access_token` - For API authentication
- `refresh_token` - For token refresh
- `user` - User profile data

## Technologies

- React 18
- React Router 6
- Material-UI 5
- Axios
- Recharts (for future data visualization)

## Development Notes

- API calls automatically include JWT token via Axios interceptor
- 401 responses automatically redirect to login
- Form validation on registration (password requirements)
- Role-based UI elements (admin, researcher, data_scientist, viewer)

## Building for Production

```bash
npm run build
```

Deploy the `build` folder to any static hosting service (Netlify, Vercel, S3, etc.)
or serve it with the Flask backend using a reverse proxy.
