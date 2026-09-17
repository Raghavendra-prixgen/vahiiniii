$(document).ready(function () {
    $('.pkg-options-btn').click(function (e) {
        e.stopPropagation();
        const $card = $(this).closest('.product-card');
        const $dialog = $card.find('.pkg-select-dialog');

        // Hide all other dialogs
        $('.pkg-select-dialog').not($dialog).hide();

        // Reset input fields and checkboxes in the dialog
        $dialog.find('input[type="radio"]').prop('checked', false);
        $dialog.find('input[type="text"]').val(''); 
        $dialog.find('.pkg-select-total span').text('0');
        $dialog.toggle();
    });

    // Handle close button of packaging dialog
    $('.pkg-select-close').click(function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).closest('.pkg-select-dialog').hide();
    });

    $(document).click(function (e) {
        if (!$(e.target).closest('.pkg-select-dialog, .pkg-options-btn').length) {
            $('.pkg-select-dialog').hide();
        }
    });

    $('.product-card').each(function () {
        const productId = $(this).attr('value');

        // Handle package selection
        $(`input[name="pkg_option_${productId}"]`).change(function () {
            updatePackageTotal(productId);
        });

        // Handle package count change
        $(`#pkg_count_${productId}`).on('input', function () {
            updatePackageTotal(productId);
        });
    });

    function updatePackageTotal(productId) {
        const selectedPackage = $(`input[name="pkg_option_${productId}"]:checked`);
        const packCount = parseInt($(`#pkg_count_${productId}`).val()) || 0;

        if (selectedPackage.length && packCount > 0) {
            const unitsPerPack = parseInt(selectedPackage.val());
            const total = unitsPerPack * packCount;
            $(`#pkg_total_units_${productId}`).text(total);
        } else {
            $(`#pkg_total_units_${productId}`).text('0');
        }
    }

    $('.pkg-select-dialog').on('click', 'button', function (e) {
        e.preventDefault();
    });


    $(document).on("click", ".pkg-select-save", function (e) {
        e.preventDefault();
        var productCard = $(this).closest(".pkg-select-dialog").prev();  // Get the product card
        var pkgDialog = $(this).closest(".pkg-select-dialog");

        // Close the package dialog
        pkgDialog.hide();

        // Store package details
        let productId = productCard.attr("value");
        let selectedPackage = pkgDialog.find('input[type="radio"]:checked');
        let packageId = selectedPackage.attr('id');
        let noOfPackagesRequired = pkgDialog.find('.pkg-select-quantity input').val();

        // Calculate total quantity
        let totalQuantity = parseInt(pkgDialog.find(".pkg-select-total span").text().trim()) || 0;
        if (totalQuantity > 0) {
            var productFooter = productCard.find(".product-card-foot");
            var addButton = productFooter.find(".add-button");
            var quantityControls = productFooter.find(".quantity-controls");

            if (quantityControls.length === 0) {
                // Hide the Add button
                addButton.hide();

                // Create and append quantity controls
                var quantityControlsHtml = $(`
                    <div class="quantity-controls d-flex align-items-center" data-package-id="${packageId}" data-package_nos="${noOfPackagesRequired}" data-totalQuantity="${totalQuantity}">
                        <button class="minus-btn btn btn-sm">-</button>
                        <input type="text" class="quantity_value mx-1" value="${totalQuantity}" style="width: 40px; text-align: center;">
                        <button class="plus-btn btn btn-sm" style="margin-right: 10px;">+</button>
                        <button class="remove-button btn btn-sm"><i class="fa fa-trash" aria-hidden="true"></i></button>
                    </div>
                `);

                productFooter.append(quantityControlsHtml);

                handleQuantityControls(productFooter);
            } else {
                quantityControls.find(".quantity_value").val(totalQuantity);
            }
        }

        productCard.data('packageInfo', {
            packageId: packageId,
            noOfPackagesRequired: noOfPackagesRequired,
            totalQuantity: totalQuantity
        });

    });

    function handleQuantityControls(productFooter) {
        var quantityControls = productFooter.find(".quantity-controls");
        var quantityInput = quantityControls.find(".quantity_value");

        quantityControls.find("button").off("click").on("click", function (e) {
            e.preventDefault();
            var currentQuantity = parseInt(quantityInput.val()) || 1;

            if ($(this).hasClass("minus-btn")) {
                if (currentQuantity > 1) {
                    quantityInput.val(currentQuantity - 1);
                } else {
                    quantityControls.remove();
                    productFooter.html('<button class="add-button" type="button">Add</button>');
                }
            } else if ($(this).hasClass("plus-btn")) {
                quantityInput.val(currentQuantity + 1);
            } else if ($(this).hasClass("remove-button")) {
                quantityControls.remove();
                productFooter.html('<button class="add-button" type="button">Add</button>');
            }
        });
    }
});
