# Web Interface for Issue Analysis Project

This web application serves as an interface for the existing issue analysis project. It provides a user-friendly way to interact with the backend services and visualize data.

## Project Structure

- **public/**: Contains static files.
  - **index.html**: Main HTML document.
  - **styles.css**: Styles for the web application.

- **src/**: Contains the source code for the application.
  - **components/**: Reusable components.
    - **App.js**: Main application component.
    - **Header.js**: Navigation and branding component.
    - **Footer.js**: Footer component with copyright information.
  - **pages/**: Page components for different routes.
    - **Home.js**: Home page component.
    - **Analysis.js**: Component for displaying analysis results.
    - **Report.js**: Component for displaying reports.
  - **services/**: API service for backend communication.
    - **api.js**: Functions for making API calls.
  - **App.js**: Integrates routing and page components.
  - **index.js**: Entry point for the React application.
  - **App.css**: Styles specific to the App component.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd web-interface
   ```

3. Install dependencies:
   ```
   npm install
   ```

## Usage

To start the development server, run:
```
npm start
```

Open your browser and navigate to `http://localhost:3000` to view the application.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.