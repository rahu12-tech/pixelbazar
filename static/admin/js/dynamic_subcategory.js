django.jQuery(document).ready(function($) {
    $('#id_category').change(function() {
        var categoryId = $(this).val();
        var subcategoryField = $('#id_subcategory');
        
        if (categoryId) {
            $.ajax({
                url: '/admin/get-subcategories/',
                data: { 'category_id': categoryId },
                success: function(data) {
                    subcategoryField.empty();
                    subcategoryField.append('<option value="">---------</option>');
                    $.each(data.subcategories, function(index, item) {
                        subcategoryField.append('<option value="' + item.id + '">' + item.name + '</option>');
                    });
                }
            });
        } else {
            subcategoryField.empty();
            subcategoryField.append('<option value="">---------</option>');
        }
    });
});