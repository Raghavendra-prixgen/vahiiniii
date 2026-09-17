from odoo import _, api, exceptions, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _purchase_request_confirm_message_content(self, request, request_dict=None):
        self.ensure_one()
        if not request_dict:
            request_dict = {}
        title = _("Order confirmation %(po_name)s for your Request %(pr_name)s") % {
            "po_name": self.name,
            "pr_name": request.name,
        }
        message = "<h3>%s</h3><ul>" % title
        message += _(
            "The following requested items from Purchase Request %(pr_name)s "
            "have now been confirmed in Purchase Order %(po_name)s:"
        ) % {
            "po_name": self.name,
            "pr_name": request.name,
        }

        for line in request_dict.values():
            message += _(
                "<li><b>%(prl_name)s</b>: Ordered quantity %(prl_qty)s %(prl_uom)s, "
                "Planned date %(prl_date_planned)s</li>"
            ) % {
                "prl_name": line["name"],
                "prl_qty": line["product_qty"],
                "prl_uom": line["product_uom"],
                "prl_date_planned": line["date_planned"],
            }
        message += "</ul>"
        return message

    def _purchase_request_confirm_message(self):
        request_obj = self.env["purchase.request"]
        for po in self:
            requests_dict = {}
            for line in po.order_line:
                for request_line in line.sudo().purchase_request_lines:
                    request_id = request_line.request_id.id
                    if request_id not in requests_dict:
                        requests_dict[request_id] = {}
                    date_planned = "%s" % line.date_planned
                    data = {
                        "name": request_line.name,
                        "product_qty": line.product_qty,
                        "product_uom": line.product_uom.name,
                        "date_planned": date_planned,
                    }
                    requests_dict[request_id][request_line.id] = data
            for request_id in requests_dict:
                request = request_obj.sudo().browse(request_id)
                message = po._purchase_request_confirm_message_content(
                    request, requests_dict[request_id]
                )
                request.message_post(
                    body=message, subtype_id=self.env.ref("mail.mt_comment").id
                )
        return True

    def button_confirm(self):
        self.order_line.purchase_line_request_line_check()
        res = super(PurchaseOrder, self).button_confirm()
        self.date_approve = self.date_order
        self._purchase_request_confirm_message()
        return res

    def button_approve(self,force=False):
        self.order_line.purchase_line_request_line_check()
        res = super(PurchaseOrder, self).button_approve(force)
        return res

    
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    purchase_request_lines = fields.Many2many(comodel_name="purchase.request.line",
                                              relation="purchase_request_purchase_order_line_rel",
                                              column1="purchase_order_line_id",
                                              column2="purchase_request_line_id",
                                              readonly=True,
                                              copy=False,
                                              )

    def action_open_request_line_tree_view(self):
        request_line_ids = []
        for line in self:
            request_line_ids += line.purchase_request_lines.ids
        domain = [("id", "in", request_line_ids)]
        return {
            "name": _("Purchase Request Lines"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request.line",
            "view_mode": "list,form",
            "domain": domain,
        }

    def purchase_line_request_line_check(self):
        for po_line in self:
            product_qty = sum(po_line.purchase_request_lines.mapped('product_qty'))
            purchase_done_quantity = sum(po_line.purchase_request_lines.purchase_lines.filtered(lambda x:x.state in ('done','purchase')).mapped('product_qty'))
            if po_line.purchase_request_lines and product_qty > 0:
                if product_qty == purchase_done_quantity:
                    raise exceptions.UserError(
                            _("Purchase Request has already been completed"))
                # if product_qty < (purchase_done_quantity + po_line.product_qty):
                #     raise exceptions.UserError(_("The quantity requested exceeds the purchase request quantity."))

        return True
