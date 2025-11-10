django.jQuery(document).ready(function($) {
    console.log('Dynamic subcategory script loaded');
    
    function updateSubcategories() {
        var categoryId = $('#id_category').val();
        var subcategoryField = $('#id_subcategory');
        
        console.log('Category changed to:', categoryId);
        
        if (categoryId) {
            $.ajax({
                url: '/api/admin/get-subcategories/',
                data: { 'category_id': categoryId },
                dataType: 'json',
                success: function(data) {
                    console.log('Subcategories received:', data);
                    subcategoryField.empty();
                    subcategoryField.append('<option value="">---------</option>');
                    $.each(data.subcategories, function(index, item) {
                        subcategoryField.append('<option value="' + item.id + '">' + item.name + '</option>');
                    });
                    subcategoryField.prop('disabled', false);
                },
                error: function(xhr, status, error) {
                    console.error('AJAX Error:', error);
                    console.error('Response:', xhr.responseText);
                    subcategoryField.empty();
                    subcategoryField.append('<option value="">Error loading subcategories</option>');
                }
            });
        } else {
            subcategoryField.empty();
            subcategoryField.append('<option value="">---------</option>');
            subcategoryField.prop('disabled', true);
        }
    }
    
    // Bind change event
    $('#id_category').on('change', updateSubcategories);
    
    // Trigger on page load if category is already selected
    if ($('#id_category').val()) {
        updateSubcategories();
    }
    
    // Also disable subcategory initially if no category selected
    if (!$('#id_category').val()) {
        $('#id_subcategory').prop('disabled', true);
    }
});