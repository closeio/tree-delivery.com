$('.product').click(function() {
    var $el = $(this),
        $group = $el.parent();
    $group.find('.product.chosen').removeClass('chosen');
    $el.addClass('chosen');
});
