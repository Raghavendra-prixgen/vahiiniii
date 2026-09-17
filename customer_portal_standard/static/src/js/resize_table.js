$(document).ready(function () {
    // Add resizers to all th elements except the last one
    $('.prod_table th:not(:last-child)').each(function () {
        $(this).append('<div class="column-resizer"></div>');
    });

    let isResizing = false;
    let currentTh = null;
    let startX, startWidth;

    // Mouse down event on resizer
    $(document).on('mousedown', '.column-resizer', function (e) {
        isResizing = true;
        currentTh = $(this).parent();

        // Get initial width and mouse position
        startX = e.pageX;
        startWidth = currentTh.width();

        // Add resize active class
        $('body').addClass('resize-active');
        $(this).addClass('resizing');

        e.preventDefault();
    });

    // Mouse move event
    $(document).on('mousemove', function (e) {
        if (!isResizing) return;

        // Calculate width change
        const widthChange = e.pageX - startX;
        const newWidth = startWidth + widthChange;

        // Minimum width check
        if (newWidth >= 50) {
            // Update th width
            currentTh.width(newWidth);

            // Update corresponding td widths
            const columnIndex = currentTh.index();
            $('.prod_table tbody tr').each(function () {
                $(this).find(`td:eq(${columnIndex})`).width(newWidth);
            });

            // Update add_itm_block td widths
            $('.add_itm_block').find(`td:eq(${columnIndex})`).width(newWidth);
        }
    });

    // Mouse up event
    $(document).on('mouseup', function () {
        if (isResizing) {
            isResizing = false;
            currentTh = null;
            $('body').removeClass('resize-active');
            $('.column-resizer').removeClass('resizing');
        }
    });

    // Store original widths
    const originalWidths = {};
    $('.prod_table th').each(function (index) {
        const width = $(this).attr('style') ?
            $(this).attr('style').match(/width:\s*([^;]+)/)?.[1] : null;
        if (width) {
            originalWidths[index] = width;
            // Set initial width
            const columnIndex = $(this).index();
            $('.prod_table tbody tr').each(function () {
                $(this).find(`td:eq(${columnIndex})`).width(width);
            });
        }
    });

    // Double click to reset to original width
    $(document).on('dblclick', '.column-resizer', function () {
        const th = $(this).parent();
        const columnIndex = th.index();
        const originalWidth = originalWidths[columnIndex];

        if (originalWidth) {
            th.width(originalWidth);
            $('.prod_table tbody tr').each(function () {
                $(this).find(`td:eq(${columnIndex})`).width(originalWidth);
            });
            $('.add_itm_block').find(`td:eq(${columnIndex})`).width(originalWidth);
        }
    });
});