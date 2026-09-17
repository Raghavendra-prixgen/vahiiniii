from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AutoLotConfiguration(models.Model):
    _name = 'auto.lot.configuration'
    _description = 'Auto Lot Creation Configuration'

    name = fields.Char(string='Name', required=True)
    product_category_id = fields.Many2one('product.category', string='Product Category', required=True)
    use_po_number = fields.Boolean(string='Use PO Number')
    use_grn_number = fields.Boolean(string='Use GRN Number')
    use_vendor_ref = fields.Boolean(string='Use Vendor Reference')
    prefix = fields.Char(string='Prefix')
    sequence_size = fields.Integer(string='Sequence Size', default=5)
    sequence_id = fields.Many2one('ir.sequence', string='Sequence')

    @api.model
    def create(self, vals):
        res = super(AutoLotConfiguration, self).create(vals)
        sequence = self.env['ir.sequence'].create({
            'name': f"Auto Lot Sequence - {res.name}",
            'code': f'auto.lot.{res.id}',
            'padding': res.sequence_size,
            'prefix': res.prefix or '',
        })
        res.sequence_id = sequence.id
        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            # Generate lots before validation
            picking._generate_auto_lots()
            
        # Call super after all lots have been generated
        return super(StockPicking, self).button_validate()

    def _generate_auto_lots(self):
        """Generate lot numbers for all eligible move lines in the picking"""
        self.ensure_one()
        
        # Only process incoming shipments that might need lot numbers
        if self.picking_type_code != 'incoming':
            return

        # Process each move line that needs a lot number
        for move in self.move_ids_without_package:
            if not move.product_id.tracking in ['lot', 'serial']:
                continue

            # Check if auto lot configuration exists for this product category
            config = self.env['auto.lot.configuration'].search([
                ('product_category_id', '=', move.product_id.categ_id.id)
            ], limit=1)

            if not config:
                continue

            # Generate lot numbers for move lines without lots
            for line in move.move_line_ids.filtered(lambda l: not l.lot_id and not l.lot_name):
                lot_name = self._generate_lot_name(config, move.product_id)
                if lot_name:
                    line.lot_name = lot_name

    def _generate_lot_name(self, config, product):
        """Generate a unique lot name based on configuration"""
        lot_name_parts = []

        # if config.prefix:
        #     lot_name_parts.append(config.prefix)

        if config.use_po_number and self.purchase_id:
            po_number = self.purchase_id.name[-5:] if len(self.purchase_id.name) >= 5 else self.purchase_id.name
            lot_name_parts.append(po_number)

        if config.use_grn_number:
            grn_number = self.name[-5:] if len(self.name) >= 5 else self.name
            lot_name_parts.append(grn_number)

        if config.use_vendor_ref and self.purchase_id and self.purchase_id.partner_ref:
            vendor_ref = self.purchase_id.partner_ref[-5:] if len(self.purchase_id.partner_ref) >= 5 else self.purchase_id.partner_ref
            lot_name_parts.append(vendor_ref)

        # Generate the sequence number
        sequence_number = config.sequence_id._next()
        lot_name_parts.append(sequence_number)

        lot_name = '-'.join(filter(None, lot_name_parts))

        existing_lots = self.env['stock.lot'].search_count([('name', '=', lot_name)])
        if existing_lots > 0:
            lot_name += f"-{existing_lots + 1}"

        return lot_name



 
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        for line in self:
            if not line.lot_id and not line.lot_name and line.product_id.lot_valuated:
                picking = line.move_id.picking_id  
                if picking and picking.picking_type_code == 'incoming':
                    config = self.env['auto.lot.configuration'].search([
                        ('product_category_id', '=', line.product_id.categ_id.id)
                    ], limit=1)

                    if config:
                        lot_name = picking._generate_lot_name(config, line.product_id)
                        line.lot_name = lot_name
                    else:
                        raise UserError(_("No auto lot configuration found for this product category."))

            # Raise an error if a lot/serial number is still mandatory
            if not line.lot_id and not line.lot_name and line.product_id.lot_valuated:
                raise UserError(_("Lot/Serial number is mandatory for product valuated by lot"))

        return super(StockMoveLine, self)._action_done()




# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     @api.model
#     def action_generate_lot_line_vals(self, context, mode, first_lot, count, lot_text=False):
#         if not context.get('default_product_id'):
#             raise UserError(_("No product found to generate Serials/Lots for."))
            
#         assert mode in ('generate', 'import')
#         default_vals = {}
        
#         # Extract default values from context
#         for key, value in context.items():
#             if key.startswith('default_'):
#                 default_vals[key[8:]] = value
                
#         product = self.env['product.product'].browse(default_vals['product_id'])
        
#         # Check for auto lot configuration
#         config = self.env['auto.lot.configuration'].search([
#             ('product_category_id', '=', product.categ_id.id)
#         ], limit=1)
        
#         if config and mode == 'generate':
#             return self._generate_auto_configured_lots(config, default_vals, count, first_lot)
#         elif mode == 'import':
#             # Use standard implementation for import mode
#             return super(StockMove, self).action_generate_lot_line_vals(
#                 context=context,
#                 mode=mode,
#                 first_lot=first_lot,
#                 count=count,
#                 lot_text=lot_text
#             )
            
#         # Fallback to standard behavior if no configuration is found
#         return super(StockMove, self).action_generate_lot_line_vals(
#             context=context,
#             mode=mode,
#             first_lot=first_lot,
#             count=count,
#             lot_text=lot_text
#         ) 
    
#     @api.model
#     def get_next_sequence_number(self, product_id=False, picking_id=False):
#         """Get the next sequence number for lot/serial generation"""
#         if product_id:
#             product = self.env['product.product'].browse(product_id)
#             config = self.env['auto.lot.configuration'].sudo().search([
#                 ('product_category_id', '=', product.categ_id.id)
#             ], limit=1)
#         else:
#             config = self.env['auto.lot.configuration'].sudo().search([], limit=1)

#         if not config:
#             return ''

#         sequence_parts = []
        
#         # Add prefix if configured
#         if config.prefix:
#             sequence_parts.append(config.prefix)
        
#         # Add PO number if configured
#         if config.use_po_number and picking_id:
#             picking = self.env['stock.picking'].browse(picking_id)
#             if picking.purchase_id:
#                 po_number = picking.purchase_id.name[-5:] if len(picking.purchase_id.name) >= 5 else picking.purchase_id.name
#                 sequence_parts.append(po_number)
        
#         # Add GRN number if configured
#         if config.use_grn_number and picking_id:
#             picking = self.env['stock.picking'].browse(picking_id)
#             grn_number = picking.name[-5:] if len(picking.name) >= 5 else picking.name
#             sequence_parts.append(grn_number)
        
#         # Add vendor reference if configured
#         if config.use_vendor_ref and picking_id:
#             picking = self.env['stock.picking'].browse(picking_id)
#             if picking.purchase_id and picking.purchase_id.partner_id.ref:
#                 vendor_ref = picking.purchase_id.partner_id.ref[-5:] if len(picking.purchase_id.partner_id.ref) >= 5 else picking.purchase_id.partner_id.ref
#                 sequence_parts.append(vendor_ref)
        
#         return '-'.join(sequence_parts) if sequence_parts else ''

#     def _generate_auto_configured_lots(self, config, default_vals, count, first_lot):
#         vals_list = []
#         picking_id = default_vals.get('picking_id')
#         purchase_order_id = self._get_purchase_order_id(picking_id)

#         product = self.env['product.product'].browse(default_vals['product_id'])
        
#         # Determine the correct UoM
#         product_uom_id = default_vals.get('product_uom_id', product.uom_id.id)
        
#         # Determine the correct destination location
#         location_dest_id = default_vals.get('location_dest_id')
#         if location_dest_id:
#             loc_dest = self.env['stock.location'].browse(location_dest_id)
#             loc_dest = loc_dest._get_putaway_strategy(product, default_vals.get('quantity', 1.0))
#             location_dest_id = loc_dest.id

#         for i in range(count):
#             lot_name_parts = []

#             if config.prefix:
#                 lot_name_parts.append(config.prefix)

#             if config.use_po_number and purchase_order_id:
#                 po = self.env['purchase.order'].browse(purchase_order_id)
#                 po_number = po.name[-5:] if len(po.name) >= 5 else po.name
#                 lot_name_parts.append(po_number)

#             if config.use_grn_number and picking_id:
#                 picking = self.env['stock.picking'].browse(picking_id)
#                 grn_number = picking.name[-5:] if len(picking.name) >= 5 else picking.name
#                 lot_name_parts.append(grn_number)

#             if config.use_vendor_ref and purchase_order_id:
#                 po = self.env['purchase.order'].browse(purchase_order_id)
#                 vendor = po.partner_id
#                 if vendor.ref:
#                     vendor_ref = vendor.ref[-5:] if len(vendor.ref) >= 5 else vendor.ref
#                     lot_name_parts.append(vendor_ref)

#             print(config.sequence_id.id,"ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
#             sequence_number = config.sequence_id._next()
#             print(sequence_number,"sequence_number")
#             lot_name_parts.append(sequence_number)
#             print(lot_name_parts,"lot_name_parts")

#             move_line_vals = {
#                 **default_vals,
#                 'lot_name': '-'.join(lot_name_parts),
#                 'quantity': default_vals.get('quantity', 1.0) / count,
#                 'product_uom_id': product_uom_id,
#                 'location_dest_id': location_dest_id,
#             }

#             # Format many2one values for webclient
#             for key, value in move_line_vals.items():
#                 if key in self.env['stock.move.line'] and isinstance(self.env['stock.move.line'][key], models.Model):
#                     move_line_vals[key] = {
#                         'id': value,
#                         'display_name': self.env['stock.move.line'][key].browse(value).display_name
#                     }

#             vals_list.append(move_line_vals)

#         return vals_list



#     def _get_purchase_order_id(self, picking_id):
#         if picking_id:
#             picking = self.env['stock.picking'].browse(picking_id)
#             if picking.purchase_id:
#                 return picking.purchase_id.id
#         return False


