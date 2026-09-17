from odoo import models, fields, api,_
from odoo import tools
from odoo.exceptions import ValidationError
from datetime import datetime
import json
from odoo.tools.float_utils import float_round


# class StockPickingCustomization(models.Model):
#     _inherit = "stock.picking"

    # y_dc_from_vendor = fields.Char(string='DC from Vendor')


class SubconRegisterReport(models.Model):
    _name = 'subcon.register.report'
    _description = 'Subcon Register Report'
    _auto = False

    y_po_id = fields.Many2one('purchase.order', string='PO ID')
    y_po_ref_no = fields.Char(string='PO Reference')
    y_po_ref_date = fields.Datetime(string='PO Date')
    y_vendor_id = fields.Many2one('res.partner', string='Vendor')
    y_vendor_gstn = fields.Char(string='Vendor GSTN')
    # y_dc_from_vendor = fields.Char(string='DC from Vendor')
    y_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')



    y_dc_ref_no = fields.Char(string='DC Reference')
    y_dc_validate_date = fields.Datetime(string='DC Date')
    y_dc_state = fields.Char(string='DC Status')
    y_dc_qty = fields.Float(string='DC Quantity')
    y_dc_uom_id = fields.Many2one('uom.uom', string='DC UoM')
    y_dc_product_id = fields.Many2one('product.product', string='DC Product')

    y_taxable_value = fields.Float(string='Taxable Value', compute='_compute_taxable_value')
    y_tax_amount = fields.Float(string='Tax Amount',compute='_compute_tax_amounts')
    y_total = fields.Float(string='Total Amount',compute='_compute_tax_amounts')
    y_grn_ref_no = fields.Char(string='GRN Reference')
    y_grn_validate_date = fields.Datetime(string='GRN Date')
    y_grn_qty = fields.Float(string='GRN Quantity')
    y_grn_uom_id = fields.Many2one('uom.uom', string='GRN UoM')
    y_grn_product_id = fields.Many2one('product.product', string='GRN Product')
    y_grn_done_date = fields.Datetime(string='GRN Done Date')
    y_first_dispatch_date = fields.Datetime(string='First Dispatch Date')
    y_due_days = fields.Integer(string='Days Since First Dispatch')
  
    y_tax_ids = fields.Many2many('account.tax', string='Taxes', compute='_compute_tax_ids')
    y_tax_names = fields.Char(string='Tax Amounts', compute='_compute_tax_names')
    y_tax_amounts = fields.Text(string='Tax Amounts', compute='_compute_tax_amounts')

    y_standard_price = fields.Float(string='Standard Price', compute='_compute_standard_price', store=False)
    y_svl_unit_cost = fields.Float(string='SVL Unit Cost')
    y_is_return_dc = fields.Boolean(string="Return DC")

    @api.depends('y_dc_product_id')
    def _compute_standard_price(self):
        for record in self:
            record.y_standard_price = record.y_dc_product_id.standard_price or 0.0

    @api.depends('y_svl_unit_cost', 'y_dc_qty', 'y_standard_price')
    def _compute_taxable_value(self):
        for record in self:
            unit_cost = record.y_svl_unit_cost if record.y_svl_unit_cost > 0 else record.y_standard_price
            record.y_taxable_value = float_round(unit_cost * record.y_dc_qty, precision_digits=2)

    @api.depends('y_po_id')
    def _compute_tax_ids(self):
        for record in self:
            if record.y_po_id:
                record.y_tax_ids = record.y_po_id.order_line.mapped('taxes_id')
            else:
                record.y_tax_ids = False


   

    @api.depends('y_po_id', 'y_taxable_value', 'y_dc_qty')
    def _compute_tax_amounts(self):
        for record in self:
            tax_amounts = {}
            total_tax = 0.0
            if record.y_po_id and record.y_taxable_value and record.y_dc_qty:
                if record.y_dc_qty > 0:
                    price_unit = record.y_taxable_value / record.y_dc_qty
                else:
                    price_unit = 0.0

                po_lines = record.y_po_id.order_line
                if record.y_grn_product_id:
                    po_lines = po_lines.filtered(lambda l: l.product_id.id == record.y_grn_product_id.id)

                line = po_lines[:1].ids and po_lines[0] or None

                if line:
                    for tax in line.taxes_id:
                        child_taxes = tax.children_tax_ids if tax.amount_type == 'group' else tax

                        if tax.amount_type == 'group' and child_taxes:
                            for child_tax in child_taxes:
                                child_tax_data = child_tax.compute_all(
                                    price_unit,
                                    line.order_id.currency_id,
                                    record.y_dc_qty,
                                    product=line.product_id,
                                    partner=line.order_id.partner_id
                                )
                                for t in child_tax_data['taxes']:
                                    tax_id = t['id']
                                    amount = t['amount']
                                    total_tax += amount
                                    if tax_id in tax_amounts:
                                        tax_amounts[tax_id]['amount'] += amount
                                    else:
                                        tax_amounts[tax_id] = {
                                            'name': self.env['account.tax'].browse(tax_id).name,
                                            'amount': amount
                                        }
                        else:
                            tax_data = tax.compute_all(
                                price_unit,
                                line.order_id.currency_id,
                                record.y_dc_qty,
                                product=line.product_id,
                                partner=line.order_id.partner_id
                            )
                            for t in tax_data['taxes']:
                                tax_id = t['id']
                                amount = t['amount']
                                total_tax += amount
                                if tax_id in tax_amounts:
                                    tax_amounts[tax_id]['amount'] += amount
                                else:
                                    tax_amounts[tax_id] = {
                                        'name': self.env['account.tax'].browse(tax_id).name,
                                        'amount': amount
                                    }

            for tax_id in tax_amounts:
                tax_amounts[tax_id]['amount'] = float_round(tax_amounts[tax_id]['amount'], precision_digits=2)

            record.y_tax_amounts = json.dumps(tax_amounts)
            record.y_tax_amount = float_round(total_tax, precision_digits=2)
            record.y_total = record.y_taxable_value + record.y_tax_amount


    @api.depends('y_tax_amounts')
    def _compute_tax_names(self):
        for record in self:
            tax_names = []
            if record.y_tax_amounts:
                tax_amounts = json.loads(record.y_tax_amounts)
                for tax in tax_amounts.values():
                    formatted_name = f"{tax['name']}: amount-{tax['amount']}"
                    tax_names.append(formatted_name)
            record.y_tax_names = ', '.join(tax_names)


    def action_po(self):
        context =dict(self.env.context)
        return {
                'name': ('Purchase Order'),
                'context': context,
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('purchase.purchase_order_form').id,
                'res_id': self.y_po_id.id,        
        }

    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'subcon_register_report')
        self._cr.execute("""
        CREATE OR REPLACE VIEW subcon_register_report AS (
            WITH po_receipt_moves AS (
                SELECT 
                    sm.id AS receipt_move_id,
                    sm.purchase_line_id,
                    pol.order_id AS po_id
                FROM stock_move sm
                JOIN purchase_order_line pol ON sm.purchase_line_id = pol.id
                WHERE sm.is_subcontract = TRUE
                -- AND sm.is_return = FALSE  -- Exclude return moves
            ),
            mo_input_moves AS (
                -- PO Receipt move → MO input move
                SELECT 
                    rel.move_orig_id AS mo_input_move_id,
                    rel.move_dest_id AS receipt_move_id,
                    sm.production_id AS mo_id,
                    prm.po_id
                FROM stock_move_move_rel rel
                JOIN stock_move sm ON sm.id = rel.move_orig_id
                JOIN po_receipt_moves prm ON prm.receipt_move_id = rel.move_dest_id
                
            ),
            mo_all_moves AS (
                -- Get ALL moves of the same MO using raw_material_production_id OR production_id
                SELECT 
                    sm.id AS mo_move_id, 
                    COALESCE(sm.production_id, sm.raw_material_production_id) AS mo_id,
                    mim.po_id
                FROM stock_move sm
                JOIN mo_input_moves mim ON COALESCE(sm.production_id, sm.raw_material_production_id) = mim.mo_id
                
            ),
            delivery_moves AS (
                -- DC moves whose orig_id is one of the MO moves (normal flow)
                SELECT 
                    rel.move_orig_id AS delivery_move_id, 
                    rel.move_dest_id AS mo_move_id,
                    mam.po_id,
                    'normal' as flow_type
                FROM stock_move_move_rel rel
                JOIN mo_all_moves mam ON mam.mo_move_id = rel.move_dest_id
            ),
            return_delivery_moves AS (
                -- Return DC moves that are directly linked to original DC moves
                -- Identify returns by checking if moves have origin_returned_move_id set
                SELECT DISTINCT
                    sm_return.id AS delivery_move_id,
                    NULL::integer AS mo_move_id,  -- Cast NULL to integer to match UNION type
                    prm.po_id,
                    'return' as flow_type
                FROM stock_move sm_return
                JOIN stock_picking sp_return ON sm_return.picking_id = sp_return.id
                JOIN stock_move sm_orig ON sm_return.origin_returned_move_id = sm_orig.id
                JOIN stock_move_move_rel rel ON rel.move_orig_id = sm_orig.id
                JOIN mo_all_moves mam ON mam.mo_move_id = rel.move_dest_id
                JOIN po_receipt_moves prm ON prm.po_id = mam.po_id
                WHERE sm_return.origin_returned_move_id IS NOT NULL  -- This identifies return moves
            ),
            all_delivery_moves AS (
                -- Combine normal and return delivery moves
                SELECT delivery_move_id, mo_move_id, po_id, flow_type FROM delivery_moves
                UNION ALL
                SELECT delivery_move_id, mo_move_id, po_id, flow_type FROM return_delivery_moves
            ),
            dc_moves_with_receipt AS (
                SELECT 
                    adm.po_id,
                    sm_del.id AS dc_move_id,
                    sm_del.picking_id AS dc_id,
                    sp_dc.name AS dc_ref_no,
                    sp_dc.date_done,
                    sp_dc.state,
                    adm.flow_type,
                    -- For normal flow, get receipt move through MO chain
                    CASE 
                        WHEN adm.flow_type = 'normal' THEN mo_input.receipt_move_id
                        WHEN adm.flow_type = 'return' THEN (
                            -- For returns, find the original receipt move through the return chain
                            SELECT DISTINCT prm.receipt_move_id 
                            FROM stock_move sm_return_curr
                            JOIN stock_move sm_orig ON sm_return_curr.origin_returned_move_id = sm_orig.id
                            JOIN stock_move_move_rel rel ON rel.move_orig_id = sm_orig.id
                            JOIN mo_all_moves mam_ret ON mam_ret.mo_move_id = rel.move_dest_id
                            JOIN mo_input_moves mo_input_ret ON mo_input_ret.mo_id = mam_ret.mo_id AND mo_input_ret.po_id = adm.po_id
                            JOIN po_receipt_moves prm ON prm.receipt_move_id = mo_input_ret.receipt_move_id
                            WHERE sm_return_curr.id = sm_del.id
                            LIMIT 1
                        )
                    END AS receipt_move_id,
                    adm.mo_move_id 
                FROM all_delivery_moves adm
                JOIN stock_move sm_del ON sm_del.id = adm.delivery_move_id
                JOIN stock_picking sp_dc ON sp_dc.id = sm_del.picking_id
                LEFT JOIN mo_all_moves mo_all ON mo_all.mo_move_id = adm.mo_move_id AND adm.flow_type = 'normal'
                LEFT JOIN mo_input_moves mo_input ON mo_input.mo_id = mo_all.mo_id AND mo_input.po_id = adm.po_id AND adm.flow_type = 'normal'
                
            ),
            -- Add a CTE to get unique combinations and avoid duplicates
            unique_records AS (
                SELECT DISTINCT ON (po.id, dc.dc_ref_no, sp.name, pp_grn.id, pp_dc.id)
                    po.id AS y_po_id,
                    po.name AS y_po_ref_no,
                    sm.warehouse_id AS y_warehouse_id,
                    po.date_approve AS y_po_ref_date,
                    po.partner_id AS y_vendor_id,
                    rp.vat AS y_vendor_gstn,

                    dc.dc_ref_no AS y_dc_ref_no,  -- This will be the returned DC's reference for returns
                    CASE WHEN dc.state = 'done' THEN dc.date_done ELSE NULL END AS y_dc_validate_date,
                    dc.state AS y_dc_state,

                    pp_dc.id AS y_dc_product_id,
                    ABS(sm2.product_uom_qty) AS y_dc_qty,  -- Always show absolute quantity
                    sm2.product_uom AS y_dc_uom_id,

                    CASE WHEN dc.flow_type = 'return' THEN NULL ELSE sp.name END AS y_grn_ref_no,
                    CASE WHEN dc.flow_type = 'return' THEN NULL 
                         WHEN sp.state = 'done' THEN sp.date_done 
                         ELSE NULL END AS y_grn_validate_date,

                    CASE WHEN dc.flow_type = 'return' THEN NULL ELSE pp_grn.id END AS y_grn_product_id,
                    CASE WHEN dc.flow_type = 'return' THEN NULL ELSE sm.product_uom_qty END AS y_grn_qty,
                    CASE WHEN dc.flow_type = 'return' THEN NULL ELSE sm.product_uom END AS y_grn_uom_id,

                    COALESCE(svl.unit_cost, 0) AS y_svl_unit_cost,

                    
                    dc.date_done AS y_first_dispatch_date,
                    CASE WHEN dc.flow_type = 'return' THEN NULL ELSE sp.date_done END AS y_grn_done_date,

                    CASE
                        WHEN sp.state = 'done' AND dc.date_done IS NOT NULL THEN
                            (sp.date_done::date - dc.date_done::date)
                        WHEN dc.date_done IS NOT NULL THEN
                            (CURRENT_DATE - dc.date_done::date)
                        ELSE NULL
                    END AS y_due_days,
                    
                    -- Add a field to identify return DCs
                    CASE WHEN dc.flow_type = 'return' THEN TRUE ELSE FALSE END AS y_is_return_dc

                FROM dc_moves_with_receipt dc

                JOIN stock_move sm2 ON dc.dc_move_id = sm2.id
                JOIN product_product pp_dc ON sm2.product_id = pp_dc.id
                JOIN product_template pt ON pt.id = pp_dc.product_tmpl_id
                LEFT JOIN stock_move sm ON sm.id = dc.receipt_move_id
                LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
                LEFT JOIN purchase_order po ON po.id = pol.order_id
                LEFT JOIN res_partner rp ON po.partner_id = rp.id

                LEFT JOIN stock_picking sp ON sm.picking_id = sp.id 
                LEFT JOIN product_product pp_grn ON sm.product_id = pp_grn.id

                LEFT JOIN LATERAL (
                    SELECT
                        svl.unit_cost,
                        svl.quantity
                    FROM stock_valuation_layer svl
                    WHERE svl.stock_move_id = COALESCE(dc.mo_move_id, sm2.id)  -- Use DC move for returns
                    ORDER BY svl.id DESC
                    LIMIT 1
                ) svl ON TRUE

                WHERE (sm.is_subcontract = TRUE OR dc.flow_type = 'return')  -- Include returns even without subcontract flag
                AND (sp.id IS NULL OR sp.backorder_id IS NULL)  -- Exclude backorder pickings
                
                ORDER BY po.id, dc.dc_ref_no, sp.name, pp_grn.id, pp_dc.id, dc.date_done DESC NULLS LAST
            )

            SELECT
                row_number() OVER () AS id,
                y_po_id,
                y_po_ref_no,
                y_po_ref_date,
                y_warehouse_id,
                y_vendor_id,
                y_vendor_gstn,
                y_dc_ref_no,
                y_dc_validate_date,
                y_dc_state,
                y_dc_product_id,
                y_dc_qty,
                y_dc_uom_id,
                y_grn_ref_no,
                y_grn_validate_date,
                y_grn_product_id,
                y_grn_qty,
                y_grn_uom_id,
                y_svl_unit_cost,
                y_first_dispatch_date,
                y_grn_done_date,
                y_due_days,
                y_is_return_dc
            FROM unique_records
        )
        """)

    @api.model
    def subcontracting_report(self):
        tree_view_id = self.env.ref('subcon_register_report.subcon_register_tree_view').id
        return {
            'name': ("Subcon Report"),
            'res_model': 'subcon.register.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'view_id': tree_view_id,
            'views': [[tree_view_id, 'list']],
        }