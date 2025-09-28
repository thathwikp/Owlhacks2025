# NutriMeal Frontend

A beautiful, modern frontend for the NutriMeal personalized meal recommendation system.

## Features

- **Modern UI Design**: Clean, responsive design with gradient backgrounds and smooth animations
- **User Profile Form**: Comprehensive form to collect user information including:
  - Basic demographics (age, gender, weight, height)
  - Activity level and fitness goals
  - Diet plan preferences
  - Dietary restrictions (vegetarian, vegan, etc.)
  - Ingredient exclusions
- **Nutrition Visualization**: Interactive display of:
  - Daily calorie targets
  - Macronutrient breakdown (protein, carbs, fat)
  - BMR and TDEE calculations
  - Per-meal recommendations
- **Meal Recommendations**: Beautiful cards showing:
  - Meal names and cuisine information
  - Nutritional information per meal
  - Ingredients list
  - Cooking instructions
  - Similarity scores based on user preferences
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Real-time Validation**: Form validation with helpful error messages
- **Loading States**: Smooth loading animations and progress indicators
- **Error Handling**: Graceful error handling with user-friendly messages

## Technology Stack

- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with:
  - CSS Grid and Flexbox for layouts
  - CSS Variables for theming
  - Smooth animations and transitions
  - Responsive design with media queries
- **Vanilla JavaScript**: No frameworks, pure JavaScript for:
  - API communication with the backend
  - Form handling and validation
  - Dynamic content rendering
  - Interactive features

## Getting Started

### Prerequisites

- A modern web browser (Chrome, Firefox, Safari, Edge)
- The NutriMeal backend API running on `http://localhost:8000`

### Installation

1. **Clone or download the frontend files**:
   ```
   frontend/
   ├── index.html
   ├── styles.css
   ├── script.js
   └── README.md
   ```

2. **Start the backend API**:
   ```bash
   cd ../backend
   python integrated_backend.py
   ```

3. **Open the frontend**:
   - Simply open `index.html` in your web browser
   - Or use a local server like Live Server in VS Code
   - Or use Python's built-in server:
     ```bash
     cd frontend
     python -m http.server 3000
     ```

### Usage

1. **Fill out your profile**:
   - Enter your basic information (age, gender, weight, height)
   - Select your activity level and fitness goal
   - Choose your preferred diet plan
   - Optionally add dietary restrictions and excluded ingredients

2. **Get recommendations**:
   - Click "Get My Meal Recommendations"
   - View your personalized nutrition targets
   - Browse curated meal recommendations
   - Click "Show More" on meals to see full cooking instructions

3. **Navigate the app**:
   - Use the navigation menu to jump between sections
   - Scroll smoothly through the different sections
   - Enjoy the responsive design on any device

## API Integration

The frontend communicates with the backend API using these endpoints:

- `POST /calculate-nutrition`: Get personalized nutrition targets
- `POST /recommend-meals`: Get curated meal recommendations

The app handles API errors gracefully and provides fallback content when services are unavailable.

## Customization

### Styling
- Modify `styles.css` to change colors, fonts, or layout
- CSS variables at the top of the file control the main theme colors
- All animations and transitions can be customized

### Functionality
- Update `script.js` to modify form validation rules
- Change API endpoints in the configuration section
- Add new features or modify existing behavior

### Content
- Edit `index.html` to change text content, add sections, or modify the structure
- Update the hero section, form labels, or footer information

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Performance

- Optimized for fast loading with minimal dependencies
- Uses modern CSS features for smooth animations
- Efficient JavaScript with minimal DOM manipulation
- Responsive images and optimized assets

## Accessibility

- Semantic HTML structure
- Proper ARIA labels and roles
- Keyboard navigation support
- High contrast colors for readability
- Screen reader friendly

## Contributing

Feel free to contribute improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the NutriMeal system and follows the same licensing terms.
