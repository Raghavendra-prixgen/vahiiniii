# from odoo import  fields, models, api, _

# class DimensionForJournalEntries(models.Model):
#     _inherit = 'hr.expense.sheet'
    
#     def action_sheet_move_create(self):
#         # print("______________________________________________")
#         res = super(DimensionForJournalEntries,self).action_sheet_move_create()
#         for rec in self:
#             for line in rec.account_move_id.line_ids:
                
#                 line.dimension_name_id = rec.employee_id.dimension_id.id
#                 # print(line.dimension_name_id,rec.employee_id.dimension_id,"____________________________pppppppppppppppppppppppppppp")
#                 line.dimension_value_id = rec.employee_id.dimension_value_id.id
#                 # print(line.dimension_value_id,rec.employee_id.dimension_id,"____________________________ssssssssssssssssssssssssssss")
            
#         return res
            