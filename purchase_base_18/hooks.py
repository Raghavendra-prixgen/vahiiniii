from odoo import models, fields, api, SUPERUSER_ID
import itertools

def purchase_uninstall_hook(env):
    # env = api.Environment(env, SUPERUSER_ID, {})
    
    action = env.ref('purchase.purchase_rfq')
    if action:
        action.write({'domain': False})

    action = env.ref('purchase.purchase_form_action')
    if action:
        action.write({'domain': False})
