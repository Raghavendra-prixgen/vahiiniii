# from . import controllers
from . import models


def post_init_hook(env):
    warehouse_ids = env['stock.warehouse'].sudo().search([])
    for warehouse in warehouse_ids:
    	env['btb.stock.warehouse'].sudo().create({'y_warehouse_id':warehouse.id})