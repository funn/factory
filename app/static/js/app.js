global.jQuery = require('jquery');
global.$ = global.jQuery;
require('jquery-form');
require('./jquery.formset.js');
require('bootstrap');
require('./bootstrap-datetimepicker.js');

$(function () {
    var date_split = this.baseURI.split('/');
    $('#main_table a.app_ajax').click(function (event) { // Maybe not so general?
        event.preventDefault();
        var hour = this.parentNode.parentNode.children[0].textContent;
        var hour_split = hour.split('-');
        var date = new Date(date_split[5], date_split[6] - 1, date_split[7], hour_split[0], hour_split[1]);
        window.update_form = function update_form(selector) {
            var form_options = {
                target: '#modal',
                success: function () { // Have to show errors here.
                    //setTimeout(function () {window.location.reload();}, 2000);
                }
            };
            selector.ajaxForm(form_options);
        };
        $.ajax({
            context: this,
            url: this.getAttribute('href', 2),
            data: {
                date: date.toUTCString()
            },
            success: function (data) {
                var modal = $('#modal');
                modal.html(data);
                modal.modal('show');
            }
        });
        return false;
    });
    $('#main_table a.app_confirm').click(function (event) {
        event.preventDefault();
        if (confirm('Удалить запись?')) {
            $.ajax({
                url: this.getAttribute('href', 2),
                success: function () {
                    window.location.reload();
                },
                error: function () {
                    alert('Не удалось.');
                }
            });
        }
        return false;
    });
    $('#datetimepicker').datetimepicker({
        'format': 'dd/mm/yyyy',
        'minView': 2,
        'startView': 2,
        'todayBtn': true,
        'todayHighlight': true,
        'onSelect': function (d, i) {
            if (d !== i.lastVal) {
              $(this).change();
            }
        }
    });
    $('#datetimepicker').datetimepicker('setDate', new Date(date_split[5], date_split[6] - 1, date_split[7]));
    $('#datetimepicker').change(function () {
        var str = document.baseURI;
        var date = $('#datetimepicker').datetimepicker('getDate');
        window.location = str.replace(/(.*)\/\d+\/\d+\/\d+\/$/g, '$1/' + date.getFullYear() + '/' + (date.getMonth() + 1) + '/' + date.getDate() + '/');
    });
});
