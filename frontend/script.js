// Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const profileForm = document.getElementById('profileForm');
const submitButton = document.getElementById('submitButton');
const resultsSection = document.getElementById('recommendations');
const nutritionTargets = document.getElementById('nutritionTargets');
const mealRecommendations = document.getElementById('mealRecommendations');

// State Management
let currentUserProfile = null;
let currentNutritionTargets = null;
let selectedMeals = [];
let groceryMap = new Map();

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    setupNavigation();
    setupHeaderScrollState();
});

function initializeApp() {
    console.log('NutriMeal App Initialized');
    
    // Add smooth animations to elements
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.hero-card, .form-group, .nutrition-card, .meal-card').forEach(el => {
        observer.observe(el);
    });

    // Inject minimal styles for sidebar layout
    injectPlanStyles();
}

function setupEventListeners() {
    // Form submission
    profileForm.addEventListener('submit', handleFormSubmission);
    
    // Real-time form validation
    const formInputs = profileForm.querySelectorAll('input, select');
    formInputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });

    // Smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                // With CSS scroll-padding-top, native smooth scroll will respect fixed header
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Update active nav link on scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section[id]');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            if (window.pageYOffset >= sectionTop) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

function scrollToProfile() {
    document.getElementById('profile').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

async function handleFormSubmission(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        return;
    }

    const formData = collectFormData();
    
    try {
        setLoadingState(true);
        
        // First, calculate nutrition targets
        const nutritionResponse = await calculateNutrition(formData);
        
        if (nutritionResponse.success) {
            currentNutritionTargets = nutritionResponse.data;
            displayNutritionTargets(nutritionResponse.data);
            
            // Then, get meal recommendations
            const mealsResponse = await getMealRecommendations(formData);
            
            if (mealsResponse.success) {
                displayMealRecommendations(mealsResponse);
                showResults();
            } else {
                // Show nutrition targets even if meals fail
                showResults();
                showNotification('Nutrition targets calculated successfully, but meal recommendations are currently unavailable.', 'warning');
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request. Please try again.', 'error');
    } finally {
        setLoadingState(false);
    }
}

function collectFormData() {
    const formData = new FormData(profileForm);
    const data = {};
    
    // Basic form fields
    for (let [key, value] of formData.entries()) {
        if (key === 'dietary_restrictions') {
            if (!data.dietary_restrictions) {
                data.dietary_restrictions = [];
            }
            data.dietary_restrictions.push(value);
        } else {
            data[key] = value;
        }
    }
    
    // Convert numeric fields
    data.age = parseInt(data.age);
    data.weight = parseFloat(data.weight);
    data.height = parseFloat(data.height);
    
    // Handle dietary restrictions
    if (!data.dietary_restrictions) {
        data.dietary_restrictions = [];
    }
    
    // Handle excluded ingredients
    if (data.exclude_ingredients) {
        data.exclude_ingredients = data.exclude_ingredients
            .split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0);
    } else {
        data.exclude_ingredients = [];
    }
    
    // Set default diet plan if not selected
    if (!data.diet_plan) {
        data.diet_plan = 'balanced';
    }
    
    currentUserProfile = data;
    return data;
}

async function calculateNutrition(userData) {
    const response = await fetch(`${API_BASE_URL}/calculate-nutrition`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

async function getMealRecommendations(userData) {
    const requestData = {
        user_profile: userData,
        meal_type: 'any',
        count: 6
    };
    
    const response = await fetch(`${API_BASE_URL}/recommend-meals`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
        if (response.status === 503) {
            // Service unavailable - meal recommendations not available
            return { success: false, message: 'Meal recommendation service is currently unavailable' };
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

function displayNutritionTargets(data) {
    const { calculations, macronutrients, daily_breakdown } = data;
    
    // Clear any previous breakdown block to avoid duplicates
    const existingBreakdown = document.querySelector('.nutrition-breakdown');
    if (existingBreakdown && existingBreakdown.parentNode) {
        existingBreakdown.parentNode.removeChild(existingBreakdown);
    }

    nutritionTargets.innerHTML = `
        <div class="nutrition-card calories">
            <i class="fas fa-fire"></i>
            <div class="nutrition-value">${Math.round(calculations.target_calories)}</div>
            <div class="nutrition-label">Daily Calories</div>
        </div>
        <div class="nutrition-card protein">
            <i class="fas fa-dumbbell"></i>
            <div class="nutrition-value">${Math.round(macronutrients.protein.grams)}g</div>
            <div class="nutrition-label">Protein (${macronutrients.protein.percentage}%)</div>
        </div>
        <div class="nutrition-card carbs">
            <i class="fas fa-bread-slice"></i>
            <div class="nutrition-value">${Math.round(macronutrients.carbohydrates.grams)}g</div>
            <div class="nutrition-label">Carbs (${macronutrients.carbohydrates.percentage}%)</div>
        </div>
        <div class="nutrition-card fat">
            <i class="fas fa-seedling"></i>
            <div class="nutrition-value">${Math.round(macronutrients.fat.grams)}g</div>
            <div class="nutrition-label">Fat (${macronutrients.fat.percentage}%)</div>
        </div>
    `;
    
    // Add detailed breakdown
    const breakdownHTML = `
        <div class="nutrition-breakdown">
            <h3 class="breakdown-title">
                <i class="fas fa-chart-pie"></i>
                Your Daily Nutrition Breakdown
            </h3>
            <div class="breakdown-grid">
                <div class="breakdown-item">
                    <h4>BMR</h4>
                    <div class="value">${Math.round(calculations.bmr)}</div>
                    <small>Base Metabolic Rate</small>
                </div>
                <div class="breakdown-item">
                    <h4>TDEE</h4>
                    <div class="value">${Math.round(calculations.tdee)}</div>
                    <small>Total Daily Energy</small>
                </div>
                <div class="breakdown-item">
                    <h4>Per Meal</h4>
                    <div class="value">${Math.round(daily_breakdown.calories_per_meal)}</div>
                    <small>Average Calories</small>
                </div>
                <div class="breakdown-item">
                    <h4>Goal</h4>
                    <div class="value">${formatGoal(data.user_profile.goal)}</div>
                    <small>Fitness Target</small>
                </div>
            </div>
        </div>
    `;
    
    nutritionTargets.insertAdjacentHTML('afterend', breakdownHTML);
}

function displayMealRecommendations(response) {
    if (!response.success || !response.recommended_meals || response.recommended_meals.length === 0) {
        mealRecommendations.innerHTML = `
            <div class="no-meals-message">
                <i class="fas fa-info-circle"></i>
                <h3>Meal Recommendations Unavailable</h3>
                <p>We couldn't generate meal recommendations at this time. Your nutrition targets are still available above!</p>
            </div>
        `;
        return;
    }

    // Ensure two-column layout (sidebar + main)
    ensureRecommendationLayout();

    const mealsHTML = response.recommended_meals.map((meal, idx) => {
        const mealId = slugify(meal.name) + '-' + idx;
        const ingredients = normalizeIngredients(meal.ingredients || []);
        const firstN = 6;
        const hasMore = ingredients.length > firstN;
        const visible = ingredients.slice(0, firstN);
        const hidden = hasMore ? ingredients.slice(firstN) : [];

        return `
        <div class="meal-card slide-up" data-mealid="${mealId}" data-meal='${JSON.stringify(safeMealForPlan(meal)).replace(/'/g, "&apos;")}'>
            <div class="meal-header">
                <div class="meal-name">${meal.name}</div>
                <div class="meal-meta">
                    <span><i class="fas fa-map-marker-alt"></i> ${meal.area}</span>
                    <span><i class="fas fa-tag"></i> ${meal.category}</span>
                </div>
            </div>
            <div class="meal-content">
                <div class="meal-nutrition">
                    <div class="nutrition-item">
                        <div class="value">${Math.round(meal.calories)}</div>
                        <div class="label">Calories</div>
                    </div>
                    <div class="nutrition-item">
                        <div class="value">${Math.round(meal.protein)}g</div>
                        <div class="label">Protein</div>
                    </div>
                    <div class="nutrition-item">
                        <div class="value">${Math.round(meal.carbohydrates)}g</div>
                        <div class="label">Carbs</div>
                    </div>
                    <div class="nutrition-item">
                        <div class="value">${Math.round(meal.fat)}g</div>
                        <div class="label">Fat</div>
                    </div>
                </div>

                ${ingredients.length > 0 ? `
                    <div class="meal-ingredients">
                        <h4><i class="fas fa-list"></i> Ingredients</h4>
                        <div class="ingredients-list" id="ingredients-${mealId}">
                            ${visible.map(ing => `<span class="ingredient-tag">${ing}</span>`).join('')}
                            ${hasMore ? `<button class="expand-ingredients" onclick="event.stopPropagation(); toggleIngredients('${mealId}')">More</button>` : ''}
                            ${hasMore ? `<div class="ingredients-hidden" id="ingredients-hidden-${mealId}" style="display:none;">${hidden.map(ing => `<span class='ingredient-tag'>${ing}</span>`).join('')}</div>` : ''}
                        </div>
                    </div>
                ` : ''}

                <div class="meal-instructions" id="instructions-${mealId}">
                    ${truncateText(meal.instructions || '', 150)}
                </div>

                ${(meal.instructions || '').length > 150 ? `
                    <button class="expand-button" onclick="event.stopPropagation(); toggleInstructions('${mealId}')">
                        <i class="fas fa-chevron-down"></i> Show More
                    </button>
                ` : ''}

                <div class="plan-actions">
                    <button class="add-plan-button" onclick='event.stopPropagation(); addMealToPlan(${JSON.stringify(safeMealForPlan(meal))})'>
                        <i class="fas fa-plus-circle"></i> Add to Plan
                    </button>
                </div>
            </div>
        </div>`;
    }).join('');

    const mainHTML = `
        <div class="recommendations-header">
            <h3>
                <i class="fas fa-utensils"></i>
                Your Personalized Meal Recommendations
            </h3>
            <p>Based on your profile, here are ${response.recommended_meals.length} meals tailored to your nutritional needs</p>
        </div>
        <div class="meals-grid" id="mealsGrid">
            ${mealsHTML}
        </div>
    `;
    const mainContainer = document.getElementById('recommendationMain') || mealRecommendations;
    mainContainer.innerHTML = mainHTML;
    attachMealCardClickHandlers();
    renderPlanSidebar();
}

function toggleInstructions(mealId) {
    const instructionsEl = document.getElementById(`instructions-${mealId}`);
    const button = instructionsEl.nextElementSibling;
    
    if (instructionsEl.classList.contains('expanded')) {
        instructionsEl.classList.remove('expanded');
        button.innerHTML = '<i class="fas fa-chevron-down"></i> Show More';
    } else {
        instructionsEl.classList.add('expanded');
        button.innerHTML = '<i class="fas fa-chevron-up"></i> Show Less';
    }
}

function toggleIngredients(mealId) {
    const hiddenBlock = document.getElementById(`ingredients-hidden-${mealId}`);
    if (!hiddenBlock) return;
    const btn = hiddenBlock.previousElementSibling; // the expand button
    if (hiddenBlock.style.display === 'none') {
        hiddenBlock.style.display = 'block';
        if (btn && btn.classList && btn.classList.contains('expand-ingredients')) {
            btn.textContent = 'Less';
        }
    } else {
        hiddenBlock.style.display = 'none';
        if (btn && btn.classList && btn.classList.contains('expand-ingredients')) {
            btn.textContent = 'More';
        }
    }
}

function addMealToPlan(meal) {
    selectedMeals.push(meal);
    // Update grocery map
    const ings = normalizeIngredients(meal.ingredients || []);
    ings.forEach(name => {
        const key = name.toLowerCase();
        groceryMap.set(key, (groceryMap.get(key) || 0) + 1);
    });
    renderPlanSidebar();
    showNotification(`${meal.name} added to your plan.`, 'success');
}

function removeMealFromPlan(index) {
    const [removed] = selectedMeals.splice(index, 1);
    if (removed) {
        // Decrement grocery counts
        normalizeIngredients(removed.ingredients || []).forEach(name => {
            const key = name.toLowerCase();
            const cur = groceryMap.get(key) || 0;
            if (cur <= 1) groceryMap.delete(key); else groceryMap.set(key, cur - 1);
        });
        renderPlanSidebar();
        showNotification(`${removed.name} removed from your plan.`, 'info');
    }
}

function renderPlanSidebar() {
    const sidebar = document.getElementById('planSidebar');
    if (!sidebar) return;

    const totals = selectedMeals.reduce((acc, m) => {
        acc.calories += Math.round(m.calories || 0);
        acc.protein += Math.round(m.protein || 0);
        acc.carbohydrates += Math.round(m.carbohydrates || 0);
        acc.fat += Math.round(m.fat || 0);
        return acc;
    }, { calories:0, protein:0, carbohydrates:0, fat:0 });

    const dailyTargets = currentNutritionTargets ? {
        calories: Math.round(currentNutritionTargets.calculations?.target_calories || 0),
        protein: Math.round(currentNutritionTargets.macronutrients?.protein?.grams || 0),
        carbohydrates: Math.round(currentNutritionTargets.macronutrients?.carbohydrates?.grams || 0),
        fat: Math.round(currentNutritionTargets.macronutrients?.fat?.grams || 0)
    } : null;

    const groceryItems = Array.from(groceryMap.entries())
        .sort((a,b) => b[1]-a[1])
        .slice(0, 200)
        .map(([name, count]) => `<li><span>${name}</span>${count>1?` <small>x${count}</small>`:''}</li>`)   
        .join('');

    sidebar.innerHTML = `
        <div class="plan-panel">
            <h3><i class="fas fa-calendar-check"></i> Daily Plan</h3>
            <div class="plan-macros">
                <div class="macro-row"><span>Calories</span><strong>${totals.calories}</strong>${dailyTargets?`<small>/ ${dailyTargets.calories}</small>`:''}</div>
                <div class="macro-row"><span>Protein</span><strong>${totals.protein} g</strong>${dailyTargets?`<small>/ ${dailyTargets.protein} g</small>`:''}</div>
                <div class="macro-row"><span>Carbs</span><strong>${totals.carbohydrates} g</strong>${dailyTargets?`<small>/ ${dailyTargets.carbohydrates} g</small>`:''}</div>
                <div class="macro-row"><span>Fat</span><strong>${totals.fat} g</strong>${dailyTargets?`<small>/ ${dailyTargets.fat} g</small>`:''}</div>
            </div>
            <div class="selected-meals">
                <h4>Selected Meals (${selectedMeals.length})</h4>
                <ul>
                    ${selectedMeals.map((m, i) => `
                        <li>
                            <span>${m.name}</span>
                            <button class="remove-btn" onclick="removeMealFromPlan(${i})" title="Remove"><i class="fas fa-times"></i></button>
                        </li>
                    `).join('')}
                </ul>
            </div>
            <div class="grocery-list">
                <h4><i class="fas fa-shopping-basket"></i> Grocery List</h4>
                ${groceryItems ? `<ul>${groceryItems}</ul>` : '<p><em>No items yet. Add meals to build your list.</em></p>'}
            </div>
        </div>
    `;
}

function ensureRecommendationLayout() {
    const layoutId = 'recommendationLayout';
    if (document.getElementById(layoutId)) return;
    const layout = document.createElement('div');
    layout.id = layoutId;
    layout.className = 'recommendation-layout';

    const sidebar = document.createElement('aside');
    sidebar.id = 'planSidebar';
    sidebar.className = 'plan-sidebar';

    const main = document.createElement('div');
    main.id = 'recommendationMain';
    main.className = 'plan-main';

    // Insert layout before the mealRecommendations container
    const parent = mealRecommendations.parentNode;
    parent.insertBefore(layout, mealRecommendations);
    layout.appendChild(sidebar);
    layout.appendChild(main);
}

function injectPlanStyles() {
    if (document.getElementById('planStyles')) return;
    const style = document.createElement('style');
    style.id = 'planStyles';
    style.textContent = `
    .recommendation-layout { display: grid; grid-template-columns: 320px 1fr; gap: 24px; align-items: start; }
    .plan-sidebar { position: sticky; top: 84px; }
    .plan-panel { background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.2); }
    .plan-panel h3 { margin: 0 0 12px; font-size: 1.1rem; }
    .plan-macros { display: grid; gap: 8px; margin-bottom: 12px; }
    .plan-macros .macro-row { display:flex; justify-content: space-between; align-items: baseline; font-size: .95rem; }
    .plan-macros .macro-row small { opacity: .8; margin-left: 6px; }
    .selected-meals ul, .grocery-list ul { list-style: none; padding: 0; margin: 8px 0 0; }
    .selected-meals li { display:flex; justify-content: space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,.06); }
    .remove-btn { background:none; border:none; color:#94a3b8; cursor:pointer; }
    .remove-btn:hover { color:#f87171; }
    .ingredients-hidden { margin-top: 8px; }
    .expand-ingredients { background: none; border: 1px dashed #64748b; color: #e2e8f0; padding: 4px 8px; border-radius: 8px; cursor: pointer; margin-left: 6px; }
    .plan-actions { margin-top: 12px; }
    .add-plan-button { background: #22c55e; color: #0b0f1a; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight: 600; }
    .add-plan-button:hover { filter: brightness(1.1); }
    @media (max-width: 980px) { .recommendation-layout { grid-template-columns: 1fr; } .plan-sidebar { position: relative; top: 0; } }
    `;
    document.head.appendChild(style);
}

function normalizeIngredients(rawList) {
    return (rawList || []).map(x => typeof x === 'string' ? x : (x.name || `${x.ingredient||''} ${x.measure||''}`.trim())).filter(Boolean);
}

function slugify(s) {
    return (s||'meal').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function safeMealForPlan(meal) {
    return {
        name: meal.name,
        category: meal.category,
        area: meal.area,
        calories: meal.calories,
        protein: meal.protein,
        carbohydrates: meal.carbohydrates,
        fat: meal.fat,
        ingredients: normalizeIngredients(meal.ingredients || []),
        instructions: meal.instructions || ''
    };
}

function attachMealCardClickHandlers() {
    const grid = document.getElementById('mealsGrid');
    if (!grid) return;
    grid.addEventListener('click', (e) => {
        const target = e.target;
        // Ignore clicks on control buttons
        if (target.closest('.expand-ingredients') || target.closest('.expand-button') || target.closest('.add-plan-button') || target.closest('.remove-btn')) {
            return;
        }
        const card = target.closest('.meal-card');
        if (!card) return;
        try {
            const mealData = JSON.parse(card.getAttribute('data-meal').replace(/&apos;/g, "'"));
            addMealToPlan(mealData);
        } catch (err) {
            console.warn('Could not parse meal data from card', err);
        }
    });
}

function showResults() {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#recommendations') {
            link.classList.add('active');
        }
    });
}

function setLoadingState(isLoading) {
    const submitButton = document.getElementById('submitButton');
    const buttonText = submitButton.querySelector('span');
    const loadingSpinner = submitButton.querySelector('.loading-spinner');
    
    if (isLoading) {
        submitButton.disabled = true;
        buttonText.textContent = 'Processing...';
        loadingSpinner.style.display = 'block';
        
        // Show loading overlay
        showLoadingOverlay('Calculating your personalized nutrition targets and meal recommendations...');
    } else {
        submitButton.disabled = false;
        buttonText.textContent = 'Get My Meal Recommendations';
        loadingSpinner.style.display = 'none';
        
        // Hide loading overlay
        hideLoadingOverlay();
    }
}

function showLoadingOverlay(message) {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

function validateForm() {
    let isValid = true;
    const requiredFields = ['age', 'weight', 'height', 'gender', 'activity_level', 'goal'];
    
    requiredFields.forEach(fieldName => {
        const field = document.getElementById(fieldName);
        if (!validateField({ target: field })) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(e) {
    const field = e.target;
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error state
    field.classList.remove('error');
    removeFieldError(field);
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Specific validations
    switch (field.name) {
        case 'age':
            const age = parseInt(value);
            if (value && (age < 1 || age > 120)) {
                isValid = false;
                errorMessage = 'Age must be between 1 and 120 years';
            }
            break;
            
        case 'weight':
            const weight = parseFloat(value);
            if (value && (weight < 20 || weight > 300)) {
                isValid = false;
                errorMessage = 'Weight must be between 20 and 300 kg';
            }
            break;
            
        case 'height':
            const height = parseFloat(value);
            if (value && (height < 100 || height > 250)) {
                isValid = false;
                errorMessage = 'Height must be between 100 and 250 cm';
            }
            break;
    }
    
    if (!isValid) {
        field.classList.add('error');
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

function clearFieldError(e) {
    const field = e.target;
    field.classList.remove('error');
    removeFieldError(field);
}

function showFieldError(field, message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    field.parentNode.appendChild(errorEl);
}

function removeFieldError(field) {
    const errorEl = field.parentNode.querySelector('.error-message');
    if (errorEl) {
        errorEl.remove();
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add notification styles if not already present
    if (!document.querySelector('.notification-styles')) {
        const styles = document.createElement('style');
        styles.className = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                animation: slideInRight 0.3s ease;
            }
            .notification-info { background: #667eea; color: white; }
            .notification-success { background: #38a169; color: white; }
            .notification-warning { background: #f6ad55; color: white; }
            .notification-error { background: #e53e3e; color: white; }
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 1rem;
            }
            .notification-close {
                background: none;
                border: none;
                color: currentColor;
                cursor: pointer;
                margin-left: auto;
                opacity: 0.8;
            }
            .notification-close:hover { opacity: 1; }
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        info: 'info-circle',
        success: 'check-circle',
        warning: 'exclamation-triangle',
        error: 'exclamation-circle'
    };
    return icons[type] || 'info-circle';
}

// Utility Functions
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

function formatGoal(goal) {
    const goalMap = {
        'maintain': 'Maintain',
        'mild_weight_loss': 'Lose Weight',
        'standard_weight_loss': 'Lose Weight',
        'mild_weight_gain': 'Gain Weight',
        'standard_weight_gain': 'Gain Weight'
    };
    return goalMap[goal] || goal;
}

// Export functions for global access
window.scrollToProfile = scrollToProfile;
window.toggleInstructions = toggleInstructions;
window.toggleIngredients = toggleIngredients;
window.addMealToPlan = addMealToPlan;
window.removeMealFromPlan = removeMealFromPlan;

// Add some additional interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.hero-card, .nutrition-card, .meal-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

function setupHeaderScrollState() {
    const header = document.querySelector('.header');
    const toggle = () => {
        if (!header) return;
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    };
    toggle();
    window.addEventListener('scroll', toggle, { passive: true });
}
