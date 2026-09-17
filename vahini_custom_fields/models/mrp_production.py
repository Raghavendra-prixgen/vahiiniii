# from odoo import api, fields, models, tools, _

# class MrpProductionCustom(models.Model):
# 	_inherit = 'mrp.production'


# 	bom_id = fields.Many2one(
#         'mrp.bom', 'Bill of Material',
#         readonly=True, states={'draft': [('readonly', False)]},
#         domain="""[
#         '&',
#             '|',
#                 ('company_id', '=', False),
#                 ('company_id', '=', company_id),
#             '&',
#                 '|',
#                     ('product_id','=',product_id),
#                     '&',
#                         ('product_tmpl_id.product_variant_ids','=',product_id),
#                         ('product_id','=',False),
#         ('type', '=', 'normal')]""",
#         check_company=True,
#         help="Bill of Materials allow you to define the list of required components to make a finished product.")


# class MrpProductionType(models.Model):
# 	_name = "mrp.production.type"
 
# 	name= fields.Char(store=True ,ondelete='cascade')
# 	description= fields.Text(string='Description',store=True ,ondelete='cascade')