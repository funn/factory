$(function () {
    function update_cost(product_id, quantity, target) {
        if (product_id > 0 && quantity > 0) {
            $.ajax('/admin/get_product_price/' + product_id, {
                success: function (data) {
                    target.value = data.price * quantity;
                }
            });
        }
    }
    $('#id_quantity').on('input', function() {
        var product_id = $('#id_product').val();
        var quantity = this.value;
        var target = $('#id_cost')[0];
        update_cost(product_id, quantity, target);
    });
    $('#id_product').change(function() {
        var product_id = $('#id_product').val();
        var quantity = this.value;
        var target = $('#id_cost')[0];
        update_cost(product_id, quantity, target);
    });
});
