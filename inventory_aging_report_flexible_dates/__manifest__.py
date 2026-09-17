{
    "name": "Inventory Ageing Report(Quantity/Value) - 18.0.3.0",
    "summary": """ """,
    "version": "18.0.0.1",
    "module_type": "official",
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'origin': 'base',
    "category": "Accounting",
    "depends": ['stock','account_accountant'],
    "data": [
        'security/access.xml',
        'security/ir.model.access.csv',
        'views/account_report.xml',
        'wizard/inventory_aging_wizard.xml',
    ],
    "installable": True,
}
