$(function () {
    function update_cost() {
        var product_id = $('#id_product')[0].value;
        var quantity = $('#id_quantity')[0].value;
        if (product_id > 0 && quantity > 0) {
            $.ajax('/admin/get_product_price/' + product_id, {
                success: function (data) {
                    var field = $('#id_price')[0];
                    if (!field) {
                        field = $('#id_cost')[0];
                    }
                    field.value = data.price * quantity;
                }
            });
        }
    }
    $('#id_quantity').on('input', update_cost);
    $('#id_product').change(update_cost);
});
