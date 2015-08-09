global.jQuery = require('jquery');
global.$ = global.jQuery;
require('jquery-form');
require('./jquery.formset.js');
require('bootstrap');

$(function () {
    $('#main_table a').click(function (event) { // Maybe not so general?
        event.preventDefault();
        var hour = this.parentNode.parentNode.children[0].textContent;
        $.ajax({
            context: this,
            url: this.getAttribute('href', 2),
            data: {
                hour: hour
            },
            success: function (data) {
                var modal = $('#modal');
                modal.html(data);
                $('#appointmentTime').text(hour);
                var date_split = this.baseURI.split('/');
                var hour_split = hour.split('-');
                var date = new Date(date_split[5], date_split[6] - 1, date_split[7], hour_split[0], hour_split[1]);
                var form_options = {
                    target: '#modal',
                    data: {
                        date: date.toUTCString()
                    },
                    success: function () { // Have to show errors here.
                        setTimeout(function () {window.location.reload();}, 2000);
                    },
                };
                $('#appointmentForm').ajaxForm(form_options);
                modal.modal('show');
            }
        });
        return false;
    });
});
