(function waitForDjangoJQuery(callback) {
    if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
        callback(django.jQuery);
    } else {
        setTimeout(function() {
            waitForDjangoJQuery(callback);
        }, 50);  // vuelve a intentarlo en 50ms
    }
})(function($) {
    $(document).ready(function() {
        function updateFields($inline) {
            var rewardType = $inline.find('.field-type').find('select').val();
            $inline.children().children().hide();  // Oculta todos

            $inline.find('.field-type').children().show();  // Siempre mostrar

            $inline.find('.field-is_active').children().show();  // Siempre mostrar

            $inline.find('.delete').children().show();  // Siempre mostrar

            switch (rewardType) {
                case '0': // Coins
                    $inline.find('.field-quantity').children().show();
                    break;
                case '1': // Wildcards
                    $inline.find('.field-wildcard').children().show();
                    $inline.find('.field-quantity').children().show();
                    break;
                default:
                    console.log(rewardType)
            }
        }

        $('#gifts-heading').parent().find('table').find('tbody').change(function() {
            $('.dynamic-gifts').each(function() {
                var $inline = $(this);
                updateFields($inline);
                $inline.find('.field-type').change(function() {
                    updateFields($inline);
                });
            });
        })
        $('.dynamic-gifts').each(function() {
            var $inline = $(this);
            updateFields($inline);
            $inline.find('.field-type').change(function() {
                updateFields($inline);
            });
        });
    });
})(django.jQuery);
