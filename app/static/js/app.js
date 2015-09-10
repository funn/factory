global.jQuery = require('jquery');
global.$ = global.jQuery;
require('jquery-form');
require('./jquery.formset.js');
require('bootstrap');

$(function () {
    var date_split = this.baseURI.split('/');
    $('#main_table a').click(function (event) { // Maybe not so general?
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
});
