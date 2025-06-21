# cards/widgets.py
from django import forms
from django.utils.safestring import mark_safe


class ColorPickerWidget(forms.TextInput):
    """Enhanced color picker widget with live preview"""

    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'color',
            'style': 'width: 60px; height: 40px; margin-right: 10px;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # Get the basic input HTML
        input_html = super().render(name, value, attrs, renderer)

        # Ensure we have a valid hex color
        if not value:
            value = '#000000'

        # Add live preview elements and JavaScript
        widget_html = f'''
        <div class="color-picker-container" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            {input_html}
            <span class="color-code" id="color-code-{name}" style="
                font-family: monospace; 
                padding: 8px 12px; 
                background: #f8f9fa; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                min-width: 80px; 
                font-size: 12px;
                font-weight: bold;
                color: #333;
            ">{value}</span>
            <div class="color-preview" id="color-preview-{name}" style="
                width: 30px; 
                height: 30px; 
                background: {value}; 
                border: 1px solid #ccc; 
                border-radius: 4px;
                box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
            "></div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const input = document.querySelector('input[name="{name}"]');
                const colorCode = document.getElementById('color-code-{name}');
                const preview = document.getElementById('color-preview-{name}');

                if (input && colorCode && preview) {{
                    function updatePreview() {{
                        const color = input.value;
                        colorCode.textContent = color.toUpperCase();
                        preview.style.background = color;

                        // Update the main color preview if it exists
                        updateMainColorPreview();
                    }}

                    input.addEventListener('input', updatePreview);
                    input.addEventListener('change', updatePreview);
                }}
            }});

            function updateMainColorPreview() {{
                // Only proceed if we have all the inputs
                const bgInput = document.querySelector('input[name="background_color"]');
                const accentInput = document.querySelector('input[name="accent_color"]');
                const textInput = document.querySelector('input[name="text_color"]');

                if (bgInput && accentInput && textInput) {{
                    const bgColor = bgInput.value || '#667eea';
                    const accentColor = accentInput.value || '#764ba2';
                    const textColor = textInput.value || '#ffffff';
                    const gradient = `linear-gradient(135deg, ${{bgColor}} 0%, ${{accentColor}} 100%)`;

                    // Update only the specific preview elements with class names
                    const colorPreviewField = document.querySelector('.field-color_preview');
                    if (colorPreviewField) {{
                        const bgPreview = colorPreviewField.querySelector('.bg-preview');
                        const accentPreview = colorPreviewField.querySelector('.accent-preview');
                        const textPreview = colorPreviewField.querySelector('.text-preview');
                        const gradientPreview = colorPreviewField.querySelector('.gradient-preview');

                        const bgCode = colorPreviewField.querySelector('.bg-code');
                        const accentCode = colorPreviewField.querySelector('.accent-code');
                        const textCode = colorPreviewField.querySelector('.text-code');

                        if (bgPreview) {{
                            bgPreview.style.background = bgColor;
                            bgPreview.title = `Background: ${{bgColor}}`;
                        }}
                        if (accentPreview) {{
                            accentPreview.style.background = accentColor;
                            accentPreview.title = `Accent: ${{accentColor}}`;
                        }}
                        if (textPreview) {{
                            textPreview.style.background = textColor;
                            textPreview.title = `Text: ${{textColor}}`;
                        }}
                        if (gradientPreview) {{
                            gradientPreview.style.background = gradient;
                            gradientPreview.title = `Gradient: ${{bgColor}} → ${{accentColor}}`;
                        }}

                        if (bgCode) bgCode.textContent = bgColor.toUpperCase();
                        if (accentCode) accentCode.textContent = accentColor.toUpperCase();
                        if (textCode) textCode.textContent = textColor.toUpperCase();
                    }}
                }}
            }}
        </script>
        '''

        return mark_safe(widget_html)


# Update cards/widgets.py - add this new widget

from django import forms
from django.utils.safestring import mark_safe
import json


class SearchableCountryWidget(forms.Select):
    """Searchable dropdown for country codes with flags"""

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'searchable-country-select',
            'style': 'width: 100%; min-width: 200px;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # Get all choices for JavaScript - handle Django model objects properly
        choices_data = []
        for choice_value, choice_label in self.choices:
            if choice_value:  # Skip empty choice
                # Convert model objects to their values if needed
                if hasattr(choice_value, 'pk'):
                    choice_value = choice_value.pk
                choices_data.append({
                    'value': str(choice_value),
                    'label': str(choice_label),
                })

        choices_json = json.dumps(choices_data)
        widget_id = attrs.get('id') if attrs else f'id_{name}'

        # Create the enhanced widget HTML
        widget_html = f'''
        <div class="searchable-country-container" id="container_{widget_id}">
            <style>
                .searchable-country-container {{
                    position: relative;
                    display: inline-block;
                    width: 100%;
                }}

                .country-search-input {{
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 14px;
                    background: white;
                    cursor: pointer;
                }}

                .country-search-input:focus {{
                    outline: none;
                    border-color: #0066cc;
                    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
                }}

                .country-dropdown {{
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: white;
                    border: 1px solid #ccc;
                    border-top: none;
                    border-radius: 0 0 4px 4px;
                    max-height: 200px;
                    overflow-y: auto;
                    z-index: 1000;
                    display: none;
                }}

                .country-option {{
                    padding: 8px 12px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 14px;
                }}

                .country-option:hover {{
                    background: #f0f8ff;
                }}

                .country-option.selected {{
                    background: #0066cc;
                    color: white;
                }}

                .country-flag {{
                    font-size: 18px;
                    min-width: 24px;
                }}

                .country-info {{
                    flex: 1;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .country-name {{
                    font-weight: 500;
                }}

                .country-code {{
                    color: #666;
                    font-family: monospace;
                    font-weight: bold;
                }}

                .no-results {{
                    padding: 12px;
                    text-align: center;
                    color: #666;
                    font-style: italic;
                }}
            </style>

            <input type="text" 
                   class="country-search-input" 
                   id="search_{widget_id}"
                   placeholder="🔍 Search country name or code..."
                   autocomplete="off">

            <div class="country-dropdown" id="dropdown_{widget_id}">
                <!-- Options will be populated by JavaScript -->
            </div>

            <select name="{name}" id="{widget_id}" style="display: none;">
                <option value="">---------</option>
        '''

        # Add all options to the hidden select
        for choice_value, choice_label in self.choices:
            selected = 'selected' if str(choice_value) == str(value) else ''
            widget_html += f'<option value="{choice_value}" {selected}>{choice_label}</option>'

        widget_html += f'''
            </select>

            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const container = document.getElementById('container_{widget_id}');
                    const searchInput = document.getElementById('search_{widget_id}');
                    const dropdown = document.getElementById('dropdown_{widget_id}');
                    const hiddenSelect = document.getElementById('{widget_id}');

                    const countries = {choices_json};
                    let filteredCountries = [...countries];
                    let selectedIndex = -1;

                    function updateDisplay() {{
                        const selectedValue = hiddenSelect.value;
                        const selectedCountry = countries.find(c => String(c.value) === String(selectedValue));

                        if (selectedCountry) {{
                            searchInput.value = selectedCountry.label;
                        }} else {{
                            searchInput.value = '';
                        }}
                    }}

                    function renderDropdown() {{
                        dropdown.innerHTML = '';

                        if (filteredCountries.length === 0) {{
                            dropdown.innerHTML = '<div class="no-results">No countries found</div>';
                        }} else {{
                            filteredCountries.forEach((country, index) => {{
                                const option = document.createElement('div');
                                option.className = 'country-option' + (index === selectedIndex ? ' selected' : '');

                                const parts = country.label.split(' ');
                                const flag = parts[0];
                                const name = parts.slice(1, -1).join(' ');
                                const code = parts[parts.length - 1];

                                option.innerHTML = `
                                    <span class="country-flag">${{flag}}</span>
                                    <div class="country-info">
                                        <span class="country-name">${{name}}</span>
                                        <span class="country-code">${{code}}</span>
                                    </div>
                                `;

                                option.addEventListener('click', function() {{
                                    hiddenSelect.value = country.value;
                                    updateDisplay();
                                    dropdown.style.display = 'none';
                                    selectedIndex = -1;
                                }});

                                dropdown.appendChild(option);
                            }});
                        }}
                    }}

                    function filterCountries() {{
                        const query = searchInput.value.toLowerCase();
                        filteredCountries = countries.filter(country => 
                            country.label.toLowerCase().includes(query)
                        );
                        selectedIndex = -1;
                        renderDropdown();
                    }}

                    // Event listeners
                    searchInput.addEventListener('focus', function() {{
                        filterCountries();
                        dropdown.style.display = 'block';
                    }});

                    searchInput.addEventListener('input', filterCountries);

                    searchInput.addEventListener('keydown', function(e) {{
                        if (e.key === 'ArrowDown') {{
                            e.preventDefault();
                            selectedIndex = Math.min(selectedIndex + 1, filteredCountries.length - 1);
                            renderDropdown();
                        }} else if (e.key === 'ArrowUp') {{
                            e.preventDefault();
                            selectedIndex = Math.max(selectedIndex - 1, -1);
                            renderDropdown();
                        }} else if (e.key === 'Enter') {{
                            e.preventDefault();
                            if (selectedIndex >= 0 && filteredCountries[selectedIndex]) {{
                                hiddenSelect.value = filteredCountries[selectedIndex].value;
                                updateDisplay();
                                dropdown.style.display = 'none';
                                selectedIndex = -1;
                            }}
                        }} else if (e.key === 'Escape') {{
                            dropdown.style.display = 'none';
                            selectedIndex = -1;
                        }}
                    }});

                    // Close dropdown when clicking outside
                    document.addEventListener('click', function(e) {{
                        if (!container.contains(e.target)) {{
                            dropdown.style.display = 'none';
                            selectedIndex = -1;
                            updateDisplay(); // Reset display if no valid selection
                        }}
                    }});

                    // Initialize display
                    updateDisplay();
                    renderDropdown();
                }});
            </script>
        </div>
        '''

        return mark_safe(widget_html)