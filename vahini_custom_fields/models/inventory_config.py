from odoo import  fields, models, api, _

class DepartmentStocks(models.Model):
    _name = 'department.stocks'
    _description = 'department_stocks'
    _rec_name = "y_departments"

    y_departments = fields.Char(string="Departments")

class ExpensetypeStock(models.Model):

    _name = 'expense.stocks'
    _description = 'expense_stocks'
    _rec_name = "y_expenses"

    y_expenses = fields.Char(string="Expense Type")



    
    




