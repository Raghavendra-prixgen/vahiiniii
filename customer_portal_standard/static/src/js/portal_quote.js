/** @odoo-module **/

$(document).ready(function () {

  $(".select_prod").change(function () {
    typehint();
  });

  $(".select_qty").on("keyup", function () {
    NegativeQty();
  });


  $(".submit_class").on("click", function () {
    get_create();
  });

  $('select[name="quotation_template"]').change(async function () {
    let templateId = $(this).find(":selected").attr("id");
    if (templateId && templateId != "0") {
      $.ajax({
        url: "/get_template_lines",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
          jsonrpc: "2.0",
          method: "call",
          params: {
            template_id: parseInt(templateId),
          },
        }),
        success: async function (response) {
          if (response.result) {
            let allRows = "";

            for (const element of response.result) {
              let packagingOptions = element.packaging.map(option => {
                const selected = String(option.id) === String(element.packaging_id) ? 'selected="selected"' : '';
                return `<option value="${option.id}" data-qty="${option.qty}" ${selected}>${option.name}</option>`;
              }).join('');

              allRows += `
                            <tr class="${element.product_id} ${Date.now()} product" product_id="${element.product_id}">
                                <td>${element.product_name}</td>
                                <td class="pt-3-half ${element.product_id}qty qty" contenteditable="true">${element.quantity}</td>

                                <td class="pt-3-half product_packaging_qty" contenteditable="true">
                                    ${element.packaging_qty || 0}
                                </td>
                                <td class="pt-3-half product_packaging_name">
                                    <select style="width:100%; border: none; border-radius: 0px; border-color:#8595A2;" 
                                            class="packaging_type_select form-select">
                                        <option value=""></option>
                                        ${packagingOptions}
                                    </select>
                                </td>
                                
                                <td class="pt-3-half">${element.uom}</td>
                                <td class="pt-3-half ${element.product_id}price">
                                    ${element.price.toFixed(2)}
                                </td>
                                <td class="pt-3-half ${element.product_id}amount amount">
                                    ${(element.quantity * element.price).toFixed(2)}
                                </td>
                                <td class="pt-3-half ${element.product_id}taxes">
                                    ${element.tax_name}
                                </td> 
                                <td class="pt-3-half ${element.product_id}pro_id" style="display:none;">
                                    ${element.tax_amount}
                                </td> 
                                <td class="total_am ${element.product_id}am_id">
                                    ${(element.quantity * element.price).toFixed(2)}
                                </td>
                                <td>
                                    <span class="fa fa-trash trash-icon" style="cursor: pointer;"></span>
                                </td>
                            </tr>`;
            }

            $(".data-body").append(allRows);
            updateTable();
          }
        },
        error: function (err) {
          console.error("Error fetching template lines:", err);
        },
      });
    }
  });



  function getQuantityValue(row) {
    // First try to find an input
    const quantityInput = row.find("input.select_qty");

    if (quantityInput.length > 0) {
      return parseFloat(quantityInput.val()) || 0;
    }
    const quantityCell = row.find(".qty");
    return parseFloat(quantityCell.text()) || 0;

  }

  function setQuantityValue(row, value) {
    // First try to find an input
    const quantityInput = row.find("input.select_qty");
    if (quantityInput.length > 0) {
      quantityInput.val(value.toFixed(0));
      updateTable();

    } else {
      // If no input found, update contenteditable cell
      row.find(".qty").text(value.toFixed(0));
      updateTable();
    }
  }

  // Handler for quantity changes (both input and contenteditable)
  $(document).on("input", ".select_qty, .qty", async function () {
    const row = $(this).closest("tr");
    const packagingSelect = $("tbody.data-body").find(row).find(".packaging_type_select");


    if (!packagingSelect) {
      packagingQuantityCell.text("0");
    }
    else {
      const packagingQuantityCell = row.find(".product_packaging_qty");

      // Parse values safely
      const quantity = getQuantityValue(row);
      const packagingTypeId = packagingSelect.val();
      const dataQty = parseFloat(packagingSelect.find(":selected").data("qty")) || 0;

      // Validate quantity
      if (isNaN(quantity) || quantity <= 0) {
        packagingQuantityCell.text("0");
        return;
      }

      // Update Packaging Quantity
      if (dataQty > 0) {
        const packagingQuantity = Math.ceil(quantity / dataQty);
        packagingQuantityCell.text(packagingQuantity.toFixed(0));
      } else {
        packagingQuantityCell.text("0");
      }
    }

  });

  // Handler for packaging type changes
  $(document).on("change", ".packaging_type_select", async function () {
    const row = $(this).closest("tr");
    const quantity = getQuantityValue(row);
    const packagingQuantityCell = row.find(".product_packaging_qty");
    const dataQty = parseFloat($(this).find(":selected").data("qty")) || 0;

    // Update Packaging Quantity
    if (dataQty > 0 && quantity > 0) {
      const packagingQuantity = Math.ceil(quantity / dataQty);
      packagingQuantityCell.text(packagingQuantity);
    } else {
      packagingQuantityCell.text("0");
    }
  });

  // Handler for packaging quantity updates
  $(document).on("input", ".product_packaging_qty", async function () {
    const text = $(this).text();
    if (!/^\d*$/.test(text)) {
      alert("Only numbers are allowed!");
      // Remove non-numeric characters
      $(this).text(text.replace(/\D/g, ""));
    }
    $(".product_packaging_qty").on("blur", function () {
      const text = $(this).text();
      $(this).text(text.replace(/\D/g, ""));
    });

    const row = $(this).closest("tr");
    const packagingSelect = row.find(".packaging_type_select");

    const packagingQuantity = parseFloat($(this).text()) || 0;
    const dataQty = parseFloat(packagingSelect.find(":selected").data("qty")) || 0;

    if (dataQty > 0) {
      const quantity = packagingQuantity * dataQty;
      setQuantityValue(row, quantity);
    } else {
      setQuantityValue(row, 0);
    }

    updateRowAmounts(row);

  });


  // Instead of directly binding to .trash-icon
  $(".prod_table").on("click", ".trash-icon", function () {
    let tr_cls = $(this)
      .closest("tr")
      .attr("class")
      .split(" ")
      .find((cls) => cls !== "product");

    RemoveRow(parseInt(tr_cls));
  });

  // onfocusout qty
  $(".prod_table").on("focusout", ".qty", function () {
    var tmplId = $(this).closest("tr").attr("product_id");
    EditNegativeQty(tmplId);
  });

  // Update the update_items click handler
  $(".update_items").click(function () {
    let selectedProducts = [];
    $(".product-card").each(function () {
      let productCard = $(this);

      let productId = productCard.attr("value");
      let quantityInput = productCard.find(".quantity_value");

      if (quantityInput.length > 0) {
        let quantity = parseInt(quantityInput.val());

        if (quantity > 0) {
          let productName = productCard.find(".product-title").text().trim();
          let productCode = productCard
            .find(".product-code")
            .text()
            .split(":")[1]
            .trim();

          var quantityControls = productCard.find(".quantity-controls");

          let packageId = quantityControls.attr("data-package-id");
          let noOfPackagesRequired = quantityControls.attr("data-package_nos");
          let totalQuantity = quantityControls.attr("data-totalQuantity");

          if (!productCode) {
            productName = productName
          } else {
            productName = "['" + productCode + "']" + productName
          }

          selectedProducts.push({
            productId: productId,
            productName: productName,
            productCode: productCode,
            quantity: quantity,
            packageId: packageId || null,
            noOfPackagesRequired: noOfPackagesRequired || 0,
            totalQuantity: totalQuantity || 0,
          });

          quantityControls.remove();

          productCard.find(".product-card-foot").html('<button class="add-button" type="button">Add</button>');
        }
      }
    });
    addProductRow(selectedProducts);
  });

  function handleQuantityControls(productFooter) {
    var quantityControls = productFooter.find(".quantity-controls");
    var quantityInput = quantityControls.find(".quantity_value");

    quantityControls.find("button").on("click", function (e) {
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

  // Handle ADD button click
  $(document).on("click", ".add-button", function (e) {
    e.preventDefault();
    var productFooter = $(this).parent();
    $(this).hide();

    var quantityControls = $(`
        <div class="quantity-controls d-flex align-items-center">
            <button class="minus-btn btn btn-sm">-</button>
            <input type="text" class="quantity_value mx-1" value="1" style="width: 40px; text-align: center;">
            <button class="plus-btn btn btn-sm" style="margin-right: 10px;">+</button>
            <button class="remove-button btn btn-sm"><i class="fa fa-trash" aria-hidden="true"></i></button>
        </div>
    `);

    productFooter.append(quantityControls);
    handleQuantityControls(productFooter);
  });

  $("#sortOption").on("change", function () {
    var sortOption = $(this).val();
    sortProductCards(sortOption);
  });

  function sortProductCards(sortOption) {
    var productContainer = $(".product_block");
    var productCards = productContainer.find(".product-card");

    if (sortOption === "name") {
      productCards.sort(function (a, b) {
        var nameA = $(a).find(".product-title").text().toUpperCase();
        var nameB = $(b).find(".product-title").text().toUpperCase();
        return nameA.localeCompare(nameB);
      });
    } else if (sortOption === "price") {
      productCards.sort(function (a, b) {
        var priceA = parseFloat(
          $(a)
            .find(".product-price")
            .text()
            .split(":")[1]
            .trim()
            .replace(/[^0-9.-]+/g, "")
        );
        var priceB = parseFloat(
          $(b)
            .find(".product-price")
            .text()
            .split(":")[1]
            .trim()
            .replace(/[^0-9.-]+/g, "")
        );
        return priceA - priceB;
      });
    } else if (sortOption === "code") {
      productCards.sort(function (a, b) {
        var codeA = $(a).find(".product-code").text().split(":")[1].trim();
        var codeB = $(b).find(".product-code").text().split(":")[1].trim();
        return codeA.localeCompare(codeB);
      });
    }

    productContainer.empty().append(productCards);
  }

  $("#product-search").on("keyup", function () {
    var searchText = $(this).val().toLowerCase();
    $(".product-card").each(function () {
      var productName = $(this).find(".product-title").text().toLowerCase();
      if (productName.indexOf(searchText) === -1) {
        $(this).hide();
      } else {
        $(this).show();
      }
    });
  });

  $(".add-btn").on("click", addProductRow);

  $(".btn-addrow").on("click", function () {
    resetFormFields();
  })

  function getProductPackaging(prod_id) {
    return new Promise((resolve, reject) => {
      if (prod_id && prod_id != "0") {
        $.ajax({
          url: "/get_template_lines",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
              product_id_ref: parseInt(prod_id),
            },
          }),
          success: function (response) {
            if (response.result && response.result.length > 0) {
              resolve(response.result);
            } else {
              resolve([]);
            }
          },
          error: function (err) {
            console.error("Error fetching product packaging:", err);
            reject(err);
          },
        });
      } else {
        resolve([]);
      }
    });
  }

  async function typehint() {
    let product = $(".select_prod").val();
    let product_id = product.slice(
      product.indexOf("[") + 1,
      product.indexOf("]")
    );
    let qty = $(".select_qty").val();
    let tr_cls = $.now();
    let match = $("#browsers option").filter(function () {
      return $(this).val() === product;
    });

    let tmpl_id = match.attr("tmpl_id");
    let product_uom = typeof match.attr("product_uom") === "undefined" ? "---" : match.attr("product_uom");
    let price = match.attr("price") === "undefined" ? 0 : match.attr("price");
    let amount = (qty * price).toFixed(2);
    let taxes = match.attr("taxes");
    $(".sugg_uom").text(product_uom);
    $(".sugg_price").text(price);
    $(".sugg_amount").text(amount);

    let product_list = [];
    product_list.push({
      product_id: product_id,
      quantity: qty == "" ? 1.0 : qty,
    });
    let tax_list = [];
    let tax_ids =
      typeof match.attr("taxes") === "undefined"
        ? ""
        : match
          .attr("taxes")
          .slice(
            match.attr("taxes").indexOf("[") + 1,
            match.attr("taxes").indexOf("]")
          );
    tax_list.push({ tax_id: tax_ids == "" ? "" : tax_ids });

    let tax_names = "";
    let tax_percent = 0;
    let inlc_tax = 0;

    let tx_list = get_tax_name2(tmpl_id);
    let tx_data = JSON.stringify(tx_list);
    let tx_object = JSON.parse(tx_data);
    let entries = Object.entries(tx_object);
    for (let [key, value] of entries) {
      tax_percent += parseFloat(value);
      tax_names += key + ", ";
    }

    let tax_amount = parseFloat(((tax_percent / 100) * price * qty).toFixed(2));
    inlc_tax = tax_percent > 0 ? tax_amount + parseFloat(amount) : amount;

    $(".sugg_taxes").text(tax_names);
    $(".sugg_tax_am").text(tax_amount);
    $(".sugg_total_amount").text(inlc_tax);
  }

  function NegativeQty(e) {
    if ($(".select_prod").val() == "") {
      alert("Please Select the product!");
      return false;
    }

    if ($(".select_qty").val() > 0) {
      $(".sugg_price");
    } else {
      alert("Quantity Must Greater than Zero");
      $(".sugg_amount").text("0");
      return false;
    }
    typehint();
    return true;
  }

  function updateTable() {
    let table = document.getElementById("table_id");
    let rowData = [];
    let totalSubtotal = 0;
    let total_tax_amount = 0;
    let tax_included_amount = 0;

    for (let i = 1; i < table.rows.length; i++) {
      let row = table.rows[i];
      let cells = row.cells;

      if (
        cells.length > 1 &&
        cells[cells.length - 1].innerText.trim() !== "Add"
      ) {
        let rowDataForRow = {};

        for (let j = 0; j < cells.length; j++) {
          let header = table.rows[0].cells[j].innerText.trim();
          let value = cells[j].innerText.trim();

          if (header === "Product") {
            value = value.replace(/[\[\]']/g, "").trim();
          }

          rowDataForRow[header.toLowerCase().replace(/ /g, "_")] = value;
        }

        rowData.push(rowDataForRow);

        // Validate and parse numeric values safely
        totalSubtotal += parseFloat(rowDataForRow.subtotal) || 0;
        total_tax_amount += parseFloat(rowDataForRow.tax_amount) || 0;
        tax_included_amount += parseFloat(rowDataForRow.total) || 0;
      }
    }

    $(".total_untaxed_amount").text(totalSubtotal.toFixed(2));
    $(".total_tax_val").text(total_tax_amount.toFixed(2));
    $(".total_amount").text(tax_included_amount.toFixed(2));
  }

  function EditNegativeQty(e_data) {

    console.log("e_data", e_data);

    let e = 0;
    if (typeof e_data === "number") {
      e = e_data;
    } else if (typeof e_data === "string") {
      e = parseInt(e_data);
    } else {
      let classesArray = e_data.classList.toString().split(" ");
      let p_id = parseInt(classesArray.pop());
      e = p_id;
    }

    let unit_price = parseInt(
      $("." + e + "price")
        .text()
        .trim()
    );
    let tax_percent = 0;

    let tx_list = get_tax_name2(e);
    let tx_data = JSON.stringify(tx_list);
    let tx_object = JSON.parse(tx_data);
    let entries = Object.entries(tx_object);
    for (let [key, value] of entries) {
      tax_percent += parseFloat(value);
    }

    if (typeof e_data === "number" && $("." + e + "qty").text() > 0) {
      $("." + e + "amount").text(
        ($("." + e + "qty").text() * $("." + e + "price").text()).toFixed(0)
      );
      $(".amount").attr(
        "price",
        ($("." + e + "qty").text() * $("." + e + "price").text()).toFixed(2)
      );

      let tax_val = $("." + e + "taxes").attr("value");
      $("." + e + "pro_id").text(
        ((tax_val / 100) * unit_price * $("." + e + "qty").text()).toFixed(2)
      );

      let tax_amount_value = parseFloat($("." + e + "pro_id").text());
      let sub_total_amount = parseFloat($("." + e + "amount").text());

      $("." + e + "am_id").text(
        parseFloat((tax_amount_value + sub_total_amount).toFixed(2))
      );
    }
    else if (typeof e_data !== "number" && parseFloat($("." + e + "qty").text()) > 0) {
      $("." + e + "amount").text(
        ($("." + e + "qty").text() * $("." + e + "price").text()).toFixed(0)
      );
      $(".amount").attr(
        "price",
        ($("." + e + "qty").text() * $("." + e + "price").text()).toFixed(2)
      );

      let sub_total_amount = parseFloat($("." + e + "amount").text()).toFixed(2);
      if (tax_percent) {
        let tax_amount = parseFloat(
          (tax_percent / 100) * unit_price * parseFloat($("." + e + "qty").text())
        ).toFixed(2);
        $("." + e + "pro_id").text(parseFloat(tax_amount));
        $("." + e + "am_id").text(
          (parseFloat(tax_amount) + parseFloat(sub_total_amount)).toFixed(2)
        );
      } else {
        $("." + e + "pro_id").text(0);
        $("." + e + "am_id").text(parseFloat(sub_total_amount).toFixed(2));
      }
    } else {
      alert("Quantity Must Greater than Zero");
      return false;
    }

    updateTable();
  }

  function RemoveRow(element) {

    if (typeof element === "number") {
      $("." + element).remove();
    } else {
      $(element).closest("tr").attr("timestamp");
      $(element).closest("tr").remove();
    }
    updateTable();
  }

  const parseSafe = (value) => parseFloat(value) || 0;

  async function updateRowValues(row) {
    const quantityInput = row.find(".select_qty");
    const packagingSelect = row.find(".packaging_type_select_option");
    const packagingQtyCell = row.find(".product_packaging_qty_value");
    const volumeCell = row.find(".volume_of_package_value");
    const weightCell = row.find(".weight_of_package_value");
    const tmpl_id = row.closest("tr").attr("product_id");

    const unitPrice = row.find(".sugg_price");
    const quantity = parseSafe(quantityInput.val());
    const packagingTypeId = packagingSelect.val();
    const dataQty = parseSafe(packagingSelect.find(":selected").data("qty"));

    // Update sub total and total
    const subTotal = parseFloat(unitPrice.text()) * quantity;
    $(".sugg_amount").text(subTotal.toFixed(2));

    let packagingQty = parseSafe(packagingQtyCell.val());
    if (!packagingQtyCell.is(":focus")) {
      if (!packagingQtyCell.data('manual-entry')) {
        packagingQty = (quantity > 0 && dataQty > 0) ? Math.ceil(quantity / dataQty) : 0;
        packagingQtyCell.val(packagingQty.toFixed(0));
      }
    }


  }

  $(document).on("focus", ".product_packaging_qty_value", function () {
    $(this).data('manual-entry', true);
  });


  $(document).on("input change focusout", ".select_qty, .packaging_type_select_option, .product_packaging_qty_value", async function (e) {

    $(".select_qty").on("input", function () {
      const text = $(this).text();
      if (!/^\d*$/.test(text)) {
        alert("Only numbers are allowed!");
        // Remove non-numeric characters
        $(this).text(text.replace(/\D/g, ""));
      }
    });

    $(".select_qty").on("blur", function () {
      const text = $(this).text();
      $(this).text(text.replace(/\D/g, ""));
    });

    const row = $(this).closest("tr");
    const isPackagingQty = $(this).hasClass("product_packaging_qty_value");
    const packagingSelect = row.find(".packaging_type_select_option");
    const quantityInput = row.find(".select_qty");
    const packagingQtyInput = row.find(".product_packaging_qty_value");

    if (isPackagingQty && e.type === "input") {
      const packagingQty = parseSafe($(this).val());
      const dataQty = parseSafe(packagingSelect.find(":selected").data("qty"));
      if (dataQty > 0) {
        if (!quantityInput.is(":focus")) {
          const newQty = (packagingQty * dataQty).toFixed(0);
          quantityInput.val(newQty);
        }
      }
    }

    if ($(this).hasClass("packaging_type_select_option")) {
      packagingQtyInput.data('manual-entry', false);
    }

    await updateRowValues(row);
  });
  // Function to populate packaging options for a product
  async function updatePackagingOptions(tmpl_id, row) {
    try {
      const result = await getProductPackaging(tmpl_id);
      const packagingSelect = row.find(".packaging_type_select_option");

      // If the select doesn't exist in this row, don't proceed
      if (packagingSelect.length === 0) return;

      let optionsHtml = '<option value=""></option>';

      if (result.length > 0) {
        result.forEach(item => {
          optionsHtml += `
            <option value="${item.id}" data-qty="${item.qty}">
              ${item.name}
            </option>`;
        });
      }

      $(".packaging_type_select_option").append(optionsHtml);

    } catch (err) {
      console.error("Error fetching product packaging:", err);
    }
  }


  // Event handler for product selection in the add item block
  $(".select_prod").on("change", async function () {
    const product = $(this).val();
    const row = $(this).closest("tr");
    // const $newRow = $(".data-body tr:last");
    const match = $("#browsers option").filter(function () {
      return $(this).val() === product;
    });

    if (match.length > 0) {
      const tmpl_id = match.attr("tmpl_id");
      await updatePackagingOptions(tmpl_id, row);
    }
  });


  async function addProductRow(selectedProducts = null) {

    if (selectedProducts && Array.isArray(selectedProducts)) {
      for (const productDetails of selectedProducts) {
        const {
          productName,
          quantity,
          packageId,
          noOfPackagesRequired,
          productId
        } = productDetails;

        // Find the matching product option
        let match = $("#browsers option").filter(function () {
          let option_id = $(this).attr("tmpl_id");

          console.log("option_id", option_id);
          console.log("productId", productId);

          return option_id === productId;
          // return $(this).val() === productName;
        });

        if (match.length === 0) {
          alert(`Invalid product: ${productName}`);
          continue;
        }

        let tmpl_id = match.attr("tmpl_id");
        let product_uom = match.attr("product_uom") || "---";
        let price = match.attr("price") || 0;
        let amount = (quantity * price).toFixed(2);

        let { tax_names, tax_percent, tax_amount, inlc_tax } = await calculateTaxes(tmpl_id, quantity, price);
        inlc_tax = inlc_tax.toFixed(2);
        let tr_cls = $.now();
        let packagingResult = await getProductPackaging(tmpl_id);
        let selectHtml = `
              <select style="width:100%; border: none; border-radius: 0px; border-color:#8595A2;" 
                      class="packaging_type_select form-select">
                  <option value=""></option>
          `;

        if (packagingResult && packagingResult.length > 0) {
          packagingResult.forEach(item => {
            const selected = String(item.id) === String(packageId) ? 'selected="selected"' : '';
            selectHtml += `
                      <option value="${item.id}" data-qty="${item.qty}" ${selected}>
                          ${item.name}
                      </option>`;
          });
        }
        selectHtml += '</select>';

        const newRow = `
              <tr class="${tmpl_id} ${tr_cls} product" product_id="${tmpl_id}">
                  <td>${productName}</td>
                  <td class="pt-3-half ${tmpl_id}qty qty" contenteditable="true">${quantity}</td>
                  <td class="pt-3-half product_packaging_qty" contenteditable="true">${noOfPackagesRequired}</td>
                  <td class="pt-3-half product_packaging_name">${selectHtml}</td>
                
                  <td class="pt-3-half">${product_uom}</td>
                  <td class="pt-3-half ${tmpl_id}price">${price}</td>
                  <td class="pt-3-half ${tmpl_id}amount amount" 
                      price="${$(".sugg_amount").attr("price")}">${amount}</td>
                  <td class="pt-3-half ${tmpl_id}taxes" 
                      value="${tax_percent}" 
                      price="${$(".sugg_taxes").attr("price")}">${tax_names}</td>
                  <td style="display:none;" class="pt-3-half ${tmpl_id}pro_id">${tax_amount}</td>
                  <td class="total_am ${tmpl_id}am_id">${inlc_tax}</td>
                  <td>
                      <span class="fa fa-trash trash-icon" style="cursor: pointer; border:none;"></span>
                  </td>
              </tr>
          `;
        $(".data-body").append(newRow);
      }

      resetFormFields();
      updateTable();
      return;
    }

    let product = $(".select_prod").val();
    let qty = $(".select_qty").val();

    let match = $("#browsers option").filter(function () {
      return $(this).val() === product;
    });

    if (match.length === 0) {
      alert("Please Select the valid product!");
      $(".select_prod").val("");
      return;
    }

    let tmpl_id = match.attr("tmpl_id");
    let product_uom = match.attr("product_uom") || "---";
    let price = match.attr("price") || 0;
    let amount = (qty * price).toFixed(2);

    let { tax_names, tax_percent, tax_amount, inlc_tax } = await calculateTaxes(tmpl_id, qty, price);
    let tr_cls = $.now();
    let packaging_option = $(".packaging_type_select_option option:selected");

    let packaging_id = selectedProducts?.packageId || packaging_option.val();

    let packaging_data_qty = parseFloat(packaging_option.attr("data-qty")) || 1;

    let packing_qty = 0;
    if (!packaging_id) {
      packing_qty = 0;
    } else {
      packing_qty = Math.ceil(qty / packaging_data_qty);
    }

    let packagingResult = await getProductPackaging(tmpl_id);
    let selectHtml = `
        <select style="width:100%; border: none; border-radius: 0px; border-color:#8595A2;" 
                class="packaging_type_select form-select">
            <option value=""></option>
    `;

    if (packagingResult && packagingResult.length > 0) {
      packagingResult.forEach(item => {
        const selected = String(item.id) === String(packaging_id) ? 'selected="selected"' : '';
        selectHtml += `
                <option value="${item.id}" data-qty="${item.qty}" ${selected}>
                    ${item.name}
                </option>`;
      });
    }
    selectHtml += '</select>';

    qty = parseInt(qty);

    const newRow = `
        <tr class="${tmpl_id} ${tr_cls} product" product_id="${tmpl_id}">
            <td>${product}</td>
            <td class="pt-3-half ${tmpl_id}qty qty" contenteditable="true">${qty}</td>
            <td class="pt-3-half product_packaging_qty" contenteditable="true">${packing_qty}</td>
            <td class="pt-3-half product_packaging_name">${selectHtml}</td>
            <td class="pt-3-half">${product_uom}</td>
            <td class="pt-3-half ${tmpl_id}price">${price}</td>
            <td class="pt-3-half ${tmpl_id}amount amount" price="${$(".sugg_amount").attr("price")}">${amount}</td>
            <td class="pt-3-half ${tmpl_id}taxes" value="${tax_percent}" price="${$(".sugg_taxes").attr("price")}">${tax_names}</td>
            <td style="display:none;" class="pt-3-half ${tmpl_id}pro_id">${tax_amount}</td>
            <td class="total_am ${tmpl_id}am_id">${inlc_tax}</td>
            <td>
                <span class="fa fa-trash trash-icon" style="cursor: pointer; border:none;"></span>
            </td>
        </tr>
    `;
    $(".data-body").append(newRow);

    resetFormFields();
    updateTable();
  }


  // Helper function to calculate taxes
  async function calculateTaxes(tmpl_id, qty, price) {
    let tax_names = "";
    let tax_percent = 0;

    const tx_list = await get_tax_name2(tmpl_id);
    const tx_object = JSON.parse(JSON.stringify(tx_list));

    for (const [key, value] of Object.entries(tx_object)) {
      tax_percent += parseFloat(value);
      tax_names += key + ", ";
    }

    const tax_amount = parseFloat(((tax_percent / 100) * price * qty).toFixed(2));
    const amount = (qty * price).toFixed(2);
    const inlc_tax = tax_percent > 0 ? tax_amount + parseFloat(amount) : amount;

    return { tax_names, tax_percent, tax_amount, inlc_tax };
  }

  // Helper function to reset form fields
  function resetFormFields() {
    $(".select_prod").val("");
    $(".select_qty").val("");
    $(".sugg_uom").text("");
    $(".sugg_price").text("");
    $(".product_packaging_qty_value").val(0);
    $('.packaging_type_select_option').empty();
    $(".sugg_amount").text("").attr("price", "");
    $(".sugg_taxes").text("").attr("price", "");
    $(".sugg_tax_am").text("");
    $(".sugg_total_amount").text("");
    $(".add_itm_block").hide();
    $(".add_icon").show();
  }


  function post_data(product_list) {
    let newclassdata = { product: JSON.stringify(product_list) };
    $.ajax({
      url: "/post/data",
      type: "POST",
      dataType: "text",
      data: newclassdata,
      success: function (response) {
        $("#my_form").submit();
      },
      error: function (xhr, response) {
        alert(response);
      },
    });
  }


  function get_create(id) {
    var product_list = [];
    $(".prod_table >tbody .product").each(function () {
      let $this = $(this);
      let product_tmpl_id = $this.attr("product_id");
      let quantity = $this.find(".qty").html();
      let packaging_qty = $this.find(".product_packaging_qty").html();
      let packaging_id = $this.find(".packaging_type_select").val();

      if (quantity > 0) {
        product_list.push({
          product_tmpl_id: product_tmpl_id,
          quantity: quantity,
          quotation_id: id,
          packaging_qty: packaging_qty,
          packaging_id: packaging_id,
        });
      } else {
        alert("Please Enter the Valid Quantity");
      }
    });

    if (product_list.length > 0) {
      product_list.push({ quotation_id: id });
      product_list.push({ 'y_delivered_to': typeof $('.delivered_to').val() === "undefined" ? " " : $('.delivered_to').val() });

      post_data(product_list);
    } else {
      alert("Please add the product to confirm!");
    }
  }

  function get_tax_name2(tmpl_id) {
    let res = "";
    $.ajax({
      url: "/get/tax/list",
      type: "POST",
      async: false,
      dataType: "text",
      data: { tmpl_id },
      success: function (response) {
        res = JSON.parse(response);
      },
      error: function (xhr, response) {
        console.err(response);
      },
    });
    return res;
  }


  async function getProductTaxDetails(product_id) {

    return new Promise((resolve, reject) => {
      if (product_id) {
        $.ajax({
          url: "/get_product_taxes",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
              product_id: parseInt(product_id),
            },
          }),
          success: function (response) {
            if (response && response.result) {
              resolve(response.result);
            } else {
              resolve({ taxes: [] });
            }
          },
          error: function (err) {
            console.error("Error fetching product taxes:", err);
            reject(err);
          },
        });
      } else {
        resolve({ taxes: [] });
      }
    });
  }

  async function updateRowAmounts(row) {
    try {
      const product_id = row.attr('product_id');
      const packagingQuantity = parseFloat(row.find('.product_packaging_qty').text()) || 0;
      const dataQty = parseFloat(row.find('.packaging_type_select :selected').data('qty')) || 0;
      const quantity = dataQty > 0 ? packagingQuantity * dataQty : 0;
      const unitPrice = parseFloat(row.find(`.${product_id}price`).text());

      // Get tax details
      const taxResult = await getProductTaxDetails(product_id);
      // Calculate amounts
      const subtotal = quantity * unitPrice;

      let totalTaxRate = 0;
      if (taxResult[0].taxes) {
        taxResult[0].taxes.forEach(tax => {
          if (tax.rate) {
            totalTaxRate += tax.rate;
          }
        });
      }

      const taxAmount = (subtotal * totalTaxRate) / 100;
      const total = subtotal + taxAmount;

      row.find(`.${product_id}amount`).text(subtotal.toFixed(2));
      row.find(`.${product_id}pro_id`).text(taxAmount.toFixed(2));
      row.find(`.${product_id}am_id`).text(total.toFixed(2));
      updateTable();

    } catch (error) {
      console.error('Error updating amounts:', error);
      // Set default values on error
      row.find('.sugg_amount, .sugg_tax_am, .sugg_total_amount, .sugg_taxes').text('0.00');
    }
  }

});

