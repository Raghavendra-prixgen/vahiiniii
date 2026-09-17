/** @odoo-module **/

$(document).ready(function () {
    // Function to apply filters
    function applyFilters() {
        var $form = $('#partner_ledger_filter_form');
        var formData = {
            date_begin: $form.find('#date_begin').val(),
            date_end: $form.find('#date_end').val(),
            journal_type: $form.find('#journal_type').val(),
            outstanding_only: $form.find('#outstanding_only').is(':checked'),
            sortby: $form.find('#sortby').val(),
        };

        // Show loading spinner
        var $container = $('#partner_ledger_table_container');
        $container.html('<div class="text-center loader-container"><div class="lds-ring"><div></div><div></div><div></div><div></div></div><p>Loading data...</p></div>');

        // Make AJAX call
        $.ajax({
            url: '/my/partner_ledger/filter',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                jsonrpc: '2.0',
                params: formData
            }),
            success: function (data) {
                if (data.result) {
                    $container.html(data.result);

                    // Update URL with new parameters without reloading the page
                    var newUrl = '/my/partner_ledger?' + $.param(formData);
                    window.history.pushState({}, '', newUrl);
                }
            },
            error: function (error) {
                $container.html('<div class="alert alert-danger">An error occurred while loading the data. Please try again.</div>');
                console.error('Error loading partner ledger data:', error);
            }
        });
    }

    // Trigger filter on input change (with debounce for better performance)
    var filterTimeout;
    $('#date_begin, #date_end, #journal_type, #sortby').on('change', function () {
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(applyFilters, 500);
    });

    // For checkbox, trigger immediately
    $('#outstanding_only').on('change', applyFilters);

    // Keep the button for manual filtering if needed
    $('#filter_apply_button').on('click', function (ev) {
        ev.preventDefault();
        applyFilters();
    });

    // Handle pagination links to use AJAX instead of page reload
    $(document).on('click', '.o_portal_pager .page-link', function (ev) {
        ev.preventDefault();

        var $link = $(this);
        var href = $link.attr('href');

        if (href) {
            // Extract page number from href
            var pageMatch = href.match(/\/page\/(\d+)/);
            var page = pageMatch ? parseInt(pageMatch[1]) : 1;

            // Get current filter values
            var $form = $('#partner_ledger_filter_form');
            var formData = {
                page: page,
                date_begin: $form.find('#date_begin').val(),
                date_end: $form.find('#date_end').val(),
                journal_type: $form.find('#journal_type').val(),
                outstanding_only: $form.find('#outstanding_only').is(':checked'),
                sortby: $form.find('#sortby').val(),
            };

            // Show loading spinner
            var $container = $('#partner_ledger_table_container');
            $container.html('<div class="text-center loader-container"><div class="lds-ring"><div></div><div></div><div></div><div></div></div><p>Loading data...</p></div>');

            // Make AJAX call
            $.ajax({
                url: '/my/partner_ledger/filter',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    jsonrpc: '2.0',
                    params: formData
                }),
                success: function (data) {
                    if (data.result) {
                        $container.html(data.result);

                        // Update URL with new parameters without reloading the page
                        var newUrl = href;
                        window.history.pushState({}, '', newUrl);
                    }
                },
                error: function (error) {
                    $container.html('<div class="alert alert-danger">An error occurred while loading the data. Please try again.</div>');
                    console.error('Error loading partner ledger data:', error);
                }
            });
        }
    });

    // // Handle PDF download button
    // $('#download_pdf_button').on('click', function (ev) {
    //     ev.preventDefault();

    //     // Get current filter values
    //     var $form = $('#partner_ledger_filter_form');
    //     var formData = {
    //         date_begin: $form.find('#date_begin').val(),
    //         date_end: $form.find('#date_end').val(),
    //         journal_type: $form.find('#journal_type').val(),
    //         outstanding_only: $form.find('#outstanding_only').is(':checked'),
    //         sortby: $form.find('#sortby').val(),
    //     };

    //     // Create URL with parameters
    //     var downloadUrl = '/my/partner_ledger/pdf?' + $.param(formData);

    //     // Redirect to download URL
    //     window.location.href = downloadUrl;
    // });

    // Handle PDF download button
    $('#download_pdf_button').on('click', function (ev) {
        ev.preventDefault();

        // Show full-screen loading overlay
        var $overlay = $('<div class="pdf-loading-overlay"><div class="pdf-loading-spinner"><div></div><div></div><div></div><div></div></div><p>Generating PDF report...</p></div>');
        $('body').append($overlay);
        $overlay.fadeIn(300);

        // Get current filter values
        var $form = $('#partner_ledger_filter_form');
        var formData = {
            date_begin: $form.find('#date_begin').val(),
            date_end: $form.find('#date_end').val(),
            journal_type: $form.find('#journal_type').val(),
            outstanding_only: $form.find('#outstanding_only').is(':checked'),
            sortby: $form.find('#sortby').val(),
        };

        // Create URL with parameters
        var downloadUrl = '/my/partner_ledger/pdf?' + $.param(formData);

        // Create a hidden iframe to handle the download
        var $iframe = $('<iframe>', {
            id: 'pdf_download_frame',
            src: downloadUrl,
            style: 'display:none'
        }).appendTo('body');

        // Remove the overlay after a timeout (since we can't detect iframe download completion reliably)
        setTimeout(function () {
            $overlay.fadeOut(300, function () {
                $overlay.remove();
            });

            // Remove the iframe after a delay
            setTimeout(function () {
                $iframe.remove();
            }, 2000);
        }, 3000);
    });


});
