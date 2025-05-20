/**
 * product-form.js - Enhances the product form with JSON field management
 */
document.addEventListener('DOMContentLoaded', function() {
    // Helper function to format JSON data in a textarea
    function formatJsonTextarea(textarea) {
        try {
            const content = textarea.value.trim();
            if (!content) return;
            
            // Parse and re-stringify to format properly
            const parsedData = JSON.parse(content);
            textarea.value = JSON.stringify(parsedData, null, 2);
        } catch (e) {
            console.warn('Could not format JSON:', e);
            // Don't modify content if it's not valid JSON
        }
    }
    
    // Format all JSON textareas on load
    document.querySelectorAll('textarea.json-field').forEach(formatJsonTextarea);
    
    // Add listeners to format JSON on blur
    document.querySelectorAll('textarea.json-field').forEach(textarea => {
        textarea.addEventListener('blur', function() {
            formatJsonTextarea(this);
        });
    });
    
    // Add JSON field managers
    setupBenefitsManager();
    setupFaqManager();
    setupTestimonialsManager();
    setupFeaturesManager();
    setupGalleryManager();
    setupBeforeAfterManager();
    setupProductComparisonManager();
    
    /**
     * Benefits list manager
     */
    function setupBenefitsManager() {
        const benefitsContainer = document.getElementById('benefits-container');
        const benefitsField = document.getElementById('benefits');
        const addBenefitBtn = document.getElementById('add-benefit');
        
        if (!benefitsContainer || !benefitsField || !addBenefitBtn) return;
        
        // Initialize from existing data
        let benefits = [];
        try {
            if (benefitsField.value.trim()) {
                benefits = JSON.parse(benefitsField.value);
            }
        } catch (e) {
            console.warn('Error parsing benefits:', e);
            benefits = [];
        }
        
        // Render benefits
        renderBenefits();
        
        // Add new benefit
        addBenefitBtn.addEventListener('click', function() {
            benefits.push({
                title: 'New Benefit',
                description: 'Describe this benefit'
            });
            renderBenefits();
            updateBenefitsField();
        });
        
        // Function to render benefits in the UI
        function renderBenefits() {
            benefitsContainer.innerHTML = '';
            
            benefits.forEach((benefit, index) => {
                const benefitDiv = document.createElement('div');
                benefitDiv.className = 'card mb-3';
                
                benefitDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Benefit Title</label>
                            <input type="text" class="form-control benefit-title" 
                                value="${benefit.title || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Benefit Description</label>
                            <textarea class="form-control benefit-description" 
                                data-index="${index}" rows="2">${benefit.description || ''}</textarea>
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-benefit" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                benefitsContainer.appendChild(benefitDiv);
            });
            
            // Add event listeners
            document.querySelectorAll('.benefit-title').forEach(input => {
                input.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    benefits[index].title = this.value;
                    updateBenefitsField();
                });
            });
            
            document.querySelectorAll('.benefit-description').forEach(textarea => {
                textarea.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    benefits[index].description = this.value;
                    updateBenefitsField();
                });
            });
            
            document.querySelectorAll('.delete-benefit').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    benefits.splice(index, 1);
                    renderBenefits();
                    updateBenefitsField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateBenefitsField() {
            benefitsField.value = JSON.stringify(benefits);
        }
    }
    
    /**
     * FAQ manager
     */
    function setupFaqManager() {
        const faqContainer = document.getElementById('faq-container');
        const faqField = document.getElementById('faq');
        const addFaqBtn = document.getElementById('add-faq');
        
        if (!faqContainer || !faqField || !addFaqBtn) return;
        
        // Initialize from existing data
        let faqItems = [];
        try {
            if (faqField.value.trim()) {
                faqItems = JSON.parse(faqField.value);
            }
        } catch (e) {
            console.warn('Error parsing FAQ:', e);
            faqItems = [];
        }
        
        // Render FAQ items
        renderFaqItems();
        
        // Add new FAQ item
        addFaqBtn.addEventListener('click', function() {
            faqItems.push({
                question: 'New Question',
                answer: 'Answer to the question'
            });
            renderFaqItems();
            updateFaqField();
        });
        
        // Function to render FAQ items in the UI
        function renderFaqItems() {
            faqContainer.innerHTML = '';
            
            faqItems.forEach((item, index) => {
                const faqDiv = document.createElement('div');
                faqDiv.className = 'card mb-3';
                
                faqDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Question</label>
                            <input type="text" class="form-control faq-question" 
                                value="${item.question || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Answer</label>
                            <textarea class="form-control faq-answer" 
                                data-index="${index}" rows="3">${item.answer || ''}</textarea>
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-faq" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                faqContainer.appendChild(faqDiv);
            });
            
            // Add event listeners
            document.querySelectorAll('.faq-question').forEach(input => {
                input.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    faqItems[index].question = this.value;
                    updateFaqField();
                });
            });
            
            document.querySelectorAll('.faq-answer').forEach(textarea => {
                textarea.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    faqItems[index].answer = this.value;
                    updateFaqField();
                });
            });
            
            document.querySelectorAll('.delete-faq').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    faqItems.splice(index, 1);
                    renderFaqItems();
                    updateFaqField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateFaqField() {
            faqField.value = JSON.stringify(faqItems);
        }
    }
    
    /**
     * Testimonials manager
     */
    function setupTestimonialsManager() {
        const testimonialsContainer = document.getElementById('testimonials-container');
        const testimonialsField = document.getElementById('testimonials');
        const addTestimonialBtn = document.getElementById('add-testimonial');
        
        if (!testimonialsContainer || !testimonialsField || !addTestimonialBtn) return;
        
        // Initialize from existing data
        let testimonials = [];
        try {
            if (testimonialsField.value.trim()) {
                testimonials = JSON.parse(testimonialsField.value);
            }
        } catch (e) {
            console.warn('Error parsing testimonials:', e);
            testimonials = [];
        }
        
        // Render testimonials
        renderTestimonials();
        
        // Add new testimonial
        addTestimonialBtn.addEventListener('click', function() {
            testimonials.push({
                author: 'Customer Name',
                text: 'What the customer said about the product',
                rating: 5,
                title: 'Job Title or Location',
                image: ''
            });
            renderTestimonials();
            updateTestimonialsField();
        });
        
        // Function to render testimonials in the UI
        function renderTestimonials() {
            testimonialsContainer.innerHTML = '';
            
            testimonials.forEach((testimonial, index) => {
                const testimonialDiv = document.createElement('div');
                testimonialDiv.className = 'card mb-3';
                
                testimonialDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Customer Name</label>
                            <input type="text" class="form-control testimonial-author" 
                                value="${testimonial.author || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Job Title/Location</label>
                            <input type="text" class="form-control testimonial-title" 
                                value="${testimonial.title || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Rating (1-5)</label>
                            <input type="number" min="1" max="5" class="form-control testimonial-rating" 
                                value="${testimonial.rating || 5}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Testimonial Text</label>
                            <textarea class="form-control testimonial-text" 
                                data-index="${index}" rows="3">${testimonial.text || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Image Path (relative to static folder)</label>
                            <input type="text" class="form-control testimonial-image" 
                                value="${testimonial.image || ''}" data-index="${index}"
                                placeholder="uploads/testimonials/image.jpg">
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-testimonial" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                testimonialsContainer.appendChild(testimonialDiv);
            });
            
            // Add event listeners for all form fields
            ['author', 'title', 'rating', 'text', 'image'].forEach(field => {
                document.querySelectorAll(`.testimonial-${field}`).forEach(input => {
                    input.addEventListener('change', function() {
                        const index = parseInt(this.dataset.index);
                        testimonials[index][field] = field === 'rating' ? parseInt(this.value) : this.value;
                        updateTestimonialsField();
                    });
                });
            });
            
            document.querySelectorAll('.delete-testimonial').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    testimonials.splice(index, 1);
                    renderTestimonials();
                    updateTestimonialsField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateTestimonialsField() {
            testimonialsField.value = JSON.stringify(testimonials);
        }
    }
    
    /**
     * Features manager
     */
    function setupFeaturesManager() {
        const featuresContainer = document.getElementById('features-container');
        const featuresField = document.getElementById('features');
        const addFeatureBtn = document.getElementById('add-feature');
        
        if (!featuresContainer || !featuresField || !addFeatureBtn) return;
        
        // Initialize from existing data
        let features = [];
        try {
            if (featuresField.value.trim()) {
                features = JSON.parse(featuresField.value);
            }
        } catch (e) {
            console.warn('Error parsing features:', e);
            features = [];
        }
        
        // Render features
        renderFeatures();
        
        // Add new feature
        addFeatureBtn.addEventListener('click', function() {
            features.push({
                title: 'New Feature',
                description: 'Describe this feature'
            });
            renderFeatures();
            updateFeaturesField();
        });
        
        // Function to render features in the UI
        function renderFeatures() {
            featuresContainer.innerHTML = '';
            
            features.forEach((feature, index) => {
                const featureDiv = document.createElement('div');
                featureDiv.className = 'card mb-3';
                
                featureDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Feature Title</label>
                            <input type="text" class="form-control feature-title" 
                                value="${feature.title || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Feature Description</label>
                            <textarea class="form-control feature-description" 
                                data-index="${index}" rows="2">${feature.description || ''}</textarea>
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-feature" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                featuresContainer.appendChild(featureDiv);
            });
            
            // Add event listeners
            document.querySelectorAll('.feature-title').forEach(input => {
                input.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    features[index].title = this.value;
                    updateFeaturesField();
                });
            });
            
            document.querySelectorAll('.feature-description').forEach(textarea => {
                textarea.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    features[index].description = this.value;
                    updateFeaturesField();
                });
            });
            
            document.querySelectorAll('.delete-feature').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    features.splice(index, 1);
                    renderFeatures();
                    updateFeaturesField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateFeaturesField() {
            featuresField.value = JSON.stringify(features);
        }
    }
    
    /**
     * Gallery images manager
     */
    function setupGalleryManager() {
        const galleryContainer = document.getElementById('gallery-container');
        const galleryField = document.getElementById('gallery_images');
        const addImageBtn = document.getElementById('add-gallery-image');
        
        if (!galleryContainer || !galleryField || !addImageBtn) return;
        
        // Initialize from existing data
        let images = [];
        try {
            if (galleryField.value.trim()) {
                images = JSON.parse(galleryField.value);
            }
        } catch (e) {
            console.warn('Error parsing gallery images:', e);
            images = [];
        }
        
        // Render gallery
        renderGallery();
        
        // Add new image
        addImageBtn.addEventListener('click', function() {
            images.push({
                path: '',
                alt: '',
                caption: ''
            });
            renderGallery();
            updateGalleryField();
        });
        
        // Function to render gallery in the UI
        function renderGallery() {
            galleryContainer.innerHTML = '';
            
            images.forEach((image, index) => {
                const imageDiv = document.createElement('div');
                imageDiv.className = 'card mb-3';
                
                imageDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Image Path (relative to static folder)</label>
                            <input type="text" class="form-control gallery-path" 
                                value="${image.path || ''}" data-index="${index}"
                                placeholder="uploads/products/image.jpg">
                        </div>
                        <div class="form-group">
                            <label>Alt Text</label>
                            <input type="text" class="form-control gallery-alt" 
                                value="${image.alt || ''}" data-index="${index}">
                        </div>
                        <div class="form-group">
                            <label>Caption (optional)</label>
                            <input type="text" class="form-control gallery-caption" 
                                value="${image.caption || ''}" data-index="${index}">
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-gallery-image" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                galleryContainer.appendChild(imageDiv);
            });
            
            // Add event listeners for all form fields
            ['path', 'alt', 'caption'].forEach(field => {
                document.querySelectorAll(`.gallery-${field}`).forEach(input => {
                    input.addEventListener('change', function() {
                        const index = parseInt(this.dataset.index);
                        images[index][field] = this.value;
                        updateGalleryField();
                    });
                });
            });
            
            document.querySelectorAll('.delete-gallery-image').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    images.splice(index, 1);
                    renderGallery();
                    updateGalleryField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateGalleryField() {
            galleryField.value = JSON.stringify(images);
        }
    }
    
    /**
     * Before/After transformations manager
     */
    function setupBeforeAfterManager() {
        const beforeAfterContainer = document.getElementById('before-after-container');
        const beforeAfterField = document.getElementById('before_after');
        const addBeforeAfterBtn = document.getElementById('add-before-after');
        
        if (!beforeAfterContainer || !beforeAfterField || !addBeforeAfterBtn) return;
        
        // Initialize from existing data
        let transformations = [];
        try {
            if (beforeAfterField.value.trim()) {
                transformations = JSON.parse(beforeAfterField.value);
            }
        } catch (e) {
            console.warn('Error parsing before/after data:', e);
            transformations = [];
        }
        
        // Render transformations
        renderBeforeAfter();
        
        // Add new transformation
        addBeforeAfterBtn.addEventListener('click', function() {
            transformations.push({
                title: 'New Transformation',
                before: 'Before state',
                after: 'After state',
                quote: ''
            });
            renderBeforeAfter();
            updateBeforeAfterField();
        });
        
        // Function to render before/after in the UI
        function renderBeforeAfter() {
            beforeAfterContainer.innerHTML = '';
            
            transformations.forEach((item, index) => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'card mb-3';
                
                itemDiv.innerHTML = `
                    <div class="card-body">
                        <div class="form-group">
                            <label>Transformation Title</label>
                            <input type="text" class="form-control ba-title" 
                                value="${item.title || ''}" data-index="${index}">
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label>Before State</label>
                                    <textarea class="form-control ba-before" 
                                        data-index="${index}" rows="3">${item.before || ''}</textarea>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label>After State</label>
                                    <textarea class="form-control ba-after" 
                                        data-index="${index}" rows="3">${item.after || ''}</textarea>
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Customer Quote (optional)</label>
                            <textarea class="form-control ba-quote" 
                                data-index="${index}" rows="2">${item.quote || ''}</textarea>
                        </div>
                        <button type="button" class="btn btn-sm btn-danger delete-ba" 
                            data-index="${index}">Remove</button>
                    </div>
                `;
                
                beforeAfterContainer.appendChild(itemDiv);
            });
            
            // Add event listeners
            ['title', 'before', 'after', 'quote'].forEach(field => {
                document.querySelectorAll(`.ba-${field}`).forEach(input => {
                    input.addEventListener('change', function() {
                        const index = parseInt(this.dataset.index);
                        transformations[index][field] = this.value;
                        updateBeforeAfterField();
                    });
                });
            });
            
            document.querySelectorAll('.delete-ba').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    transformations.splice(index, 1);
                    renderBeforeAfter();
                    updateBeforeAfterField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateBeforeAfterField() {
            beforeAfterField.value = JSON.stringify(transformations);
        }
    }
    
    /**
     * Product comparison manager
     */
    function setupProductComparisonManager() {
        const comparisonContainer = document.getElementById('comparison-container');
        const comparisonField = document.getElementById('product_comparison');
        const addCompetitorBtn = document.getElementById('add-competitor');
        const addFeatureBtn = document.getElementById('add-comparison-feature');
        
        if (!comparisonContainer || !comparisonField || !addCompetitorBtn || !addFeatureBtn) return;
        
        // Initialize from existing data
        let comparison = {
            competitors: [],
            features: []
        };
        try {
            if (comparisonField.value.trim()) {
                comparison = JSON.parse(comparisonField.value);
                if (!comparison.competitors) comparison.competitors = [];
                if (!comparison.features) comparison.features = [];
            }
        } catch (e) {
            console.warn('Error parsing product comparison data:', e);
        }
        
        // Render comparison
        renderComparison();
        
        // Add new competitor
        addCompetitorBtn.addEventListener('click', function() {
            comparison.competitors.push({
                name: 'Competitor ' + (comparison.competitors.length + 1)
            });
            renderComparison();
            updateComparisonField();
        });
        
        // Add new feature
        addFeatureBtn.addEventListener('click', function() {
            const newFeature = {
                name: 'Feature ' + (comparison.features.length + 1),
                our_value: true,
                competitor_values: []
            };
            
            // Add empty values for each competitor
            for (let i = 0; i < comparison.competitors.length; i++) {
                newFeature.competitor_values.push(false);
            }
            
            comparison.features.push(newFeature);
            renderComparison();
            updateComparisonField();
        });
        
        // Function to render comparison in the UI
        function renderComparison() {
            if (!comparisonContainer) return;
            comparisonContainer.innerHTML = '';
            
            // Competitors section
            const competitorsDiv = document.createElement('div');
            competitorsDiv.className = 'card mb-4';
            competitorsDiv.innerHTML = `
                <div class="card-header">
                    <h5>Competitors</h5>
                </div>
                <div class="card-body" id="competitors-list">
                </div>
            `;
            comparisonContainer.appendChild(competitorsDiv);
            
            const competitorsList = document.getElementById('competitors-list');
            comparison.competitors.forEach((competitor, index) => {
                const competitorDiv = document.createElement('div');
                competitorDiv.className = 'form-group d-flex align-items-center';
                competitorDiv.innerHTML = `
                    <input type="text" class="form-control competitor-name mr-2" 
                        value="${competitor.name || ''}" data-index="${index}">
                    <button type="button" class="btn btn-sm btn-danger delete-competitor" 
                        data-index="${index}">Remove</button>
                `;
                competitorsList.appendChild(competitorDiv);
            });
            
            // Features comparison table
            const featuresDiv = document.createElement('div');
            featuresDiv.className = 'card mb-4';
            featuresDiv.innerHTML = `
                <div class="card-header">
                    <h5>Feature Comparison</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-bordered" id="comparison-table">
                            <thead>
                                <tr>
                                    <th>Feature</th>
                                    <th>Our Value</th>
                                    ${comparison.competitors.map((comp, i) => 
                                        `<th>${comp.name || 'Competitor ' + (i+1)}</th>`).join('')}
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="features-list">
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            comparisonContainer.appendChild(featuresDiv);
            
            const featuresList = document.getElementById('features-list');
            comparison.features.forEach((feature, index) => {
                const row = document.createElement('tr');
                
                let competitorCells = '';
                for (let i = 0; i < comparison.competitors.length; i++) {
                    const compValue = feature.competitor_values && feature.competitor_values[i] !== undefined 
                        ? feature.competitor_values[i] 
                        : false;
                        
                    // If the value is a boolean, show a checkbox, otherwise show a text input
                    let inputHtml;
                    if (typeof compValue === 'boolean') {
                        inputHtml = `
                            <input type="checkbox" class="competitor-value" 
                                data-feature="${index}" data-competitor="${i}"
                                ${compValue ? 'checked' : ''}>
                        `;
                    } else {
                        inputHtml = `
                            <input type="text" class="form-control competitor-value-text" 
                                value="${compValue}" data-feature="${index}" data-competitor="${i}">
                        `;
                    }
                    
                    competitorCells += `<td>${inputHtml}</td>`;
                }
                
                row.innerHTML = `
                    <td>
                        <input type="text" class="form-control feature-name" 
                            value="${feature.name || ''}" data-index="${index}">
                    </td>
                    <td class="text-center">
                        <input type="checkbox" class="our-value" 
                            data-index="${index}" ${feature.our_value ? 'checked' : ''}>
                    </td>
                    ${competitorCells}
                    <td>
                        <button type="button" class="btn btn-sm btn-danger delete-feature" 
                            data-index="${index}">Remove</button>
                    </td>
                `;
                
                featuresList.appendChild(row);
            });
            
            // Add event listeners
            document.querySelectorAll('.competitor-name').forEach(input => {
                input.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    comparison.competitors[index].name = this.value;
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.delete-competitor').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    comparison.competitors.splice(index, 1);
                    
                    // Also remove this competitor's column from all features
                    comparison.features.forEach(feature => {
                        if (feature.competitor_values && feature.competitor_values.length > index) {
                            feature.competitor_values.splice(index, 1);
                        }
                    });
                    
                    renderComparison();
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.feature-name').forEach(input => {
                input.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    comparison.features[index].name = this.value;
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.our-value').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const index = parseInt(this.dataset.index);
                    comparison.features[index].our_value = this.checked;
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.competitor-value').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const featureIndex = parseInt(this.dataset.feature);
                    const competitorIndex = parseInt(this.dataset.competitor);
                    
                    if (!comparison.features[featureIndex].competitor_values) {
                        comparison.features[featureIndex].competitor_values = [];
                    }
                    
                    comparison.features[featureIndex].competitor_values[competitorIndex] = this.checked;
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.competitor-value-text').forEach(input => {
                input.addEventListener('change', function() {
                    const featureIndex = parseInt(this.dataset.feature);
                    const competitorIndex = parseInt(this.dataset.competitor);
                    
                    if (!comparison.features[featureIndex].competitor_values) {
                        comparison.features[featureIndex].competitor_values = [];
                    }
                    
                    comparison.features[featureIndex].competitor_values[competitorIndex] = this.value;
                    updateComparisonField();
                });
            });
            
            document.querySelectorAll('.delete-feature').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    comparison.features.splice(index, 1);
                    renderComparison();
                    updateComparisonField();
                });
            });
        }
        
        // Update the hidden field with JSON data
        function updateComparisonField() {
            comparisonField.value = JSON.stringify(comparison);
        }
    }
});