django.jQuery(document).ready(function($) {
    $('#id_category').change(function() {
        var categoryId = $(this).val();
        var subcategoryField = $('#id_subcategory');
        
        console.log('Category changed to:', categoryId);
        
        if (categoryId) {
            $.ajax({
                url: '/admin/get-subcategories/',
                data: { 'category_id': categoryId },
                dataType: 'json',
                success: function(data) {
                    console.log('Subcategories received:', data);
                    subcategoryField.empty();
                    subcategoryField.append('<option value="">---------</option>');
                    $.each(data.subcategories, function(index, item) {
                        subcategoryField.append('<option value="' + item.id + '">' + item.name + '</option>');
                    });
                },
                error: function(xhr, status, error) {
                    console.error('AJAX Error:', error);
                }
            });
        } else {
            subcategoryField.empty();
            subcategoryField.append('<option value="">---------</option>');
        }
    });
    
    // Trigger change on page load if category is already selected
    if ($('#id_category').val()) {
        $('#id_category').trigger('change');
    }
});