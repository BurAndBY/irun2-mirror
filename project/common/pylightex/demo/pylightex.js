(function($) {
    $.fn.katex = function(options) {
        var settings = $.extend({
            displayMode: false,
            debug: false,
            errorMessage: "error"
        }, options);

        return this.each(function() {
            var texContent = $(this).text(), element = $(this).get(0);
            try {
                katex.render(
                    texContent,
                    element, {
                        displayMode: settings.displayMode
                    }
                );
            } catch (err) {
                if (settings.debug) {
                    $(this).html("<span class='ir-err'>" + err + "<\/span>");
                } else {
                    $(this).html("<span class='ir-err'>" + settings.errorMessage + "<\/span>");
                }
            }
        });
    };
}(jQuery));
