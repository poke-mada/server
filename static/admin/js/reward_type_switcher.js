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
            var rewardType = $inline.find('.field-reward_type').find('select').val();
            $inline.children().children().hide();  // Oculta todos

            $inline.find('.field-reward_type').children().show();  // Siempre mostrar

            $inline.find('.field-is_active').children().show();  // Siempre mostrar

            $inline.find('.delete').children().show();  // Siempre mostrar

            switch (rewardType) {
                case '2': // Coins
                    console.log(rewardType);
                    $inline.find('.field-quantity').children().show();
                    break;
                case '1': // Wildcards
                    console.log(rewardType);
                    $inline.find('.field-wildcard').children().show();
                    $inline.find('.field-quantity').children().show();
                    break;
                case '0': // Item
                    console.log(rewardType);
                    $inline.find('.field-item').children().show();
                    $inline.find('.field-quantity').children().show();
                    break;
                case '3': //Pokemon
                    console.log(rewardType);
                    $inline.find('.field-pokemon_data').children().show();
                    $inline.find('.field-pokemon_pid').children().show();
                    break;
                default:
                    console.log(rewardType)
            }
        }

        $('#rewards-heading').parent().find('table').find('tbody').change(function() {
            $('.dynamic-rewards').each(function() {
                var $inline = $(this);
                updateFields($inline);
                $inline.find('.field-reward_type').change(function() {
                    console.log('awa')
                    updateFields($inline);
                });
            });
        })
        $('.dynamic-rewards').each(function() {
            var $inline = $(this);
            updateFields($inline);
            $inline.find('.field-reward_type').change(function() {
                console.log('awa')
                updateFields($inline);
            });
        });
    });
})(django.jQuery);
