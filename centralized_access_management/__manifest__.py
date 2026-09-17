{
    'name': 'Centralized Access Management (CAM) - 18.0.0.2',
    'version': '18.0.0.0',
    'category': 'Tools',
    'summary': 'User Access Management - odoo',
    'description': """
        🔑 User Access Management in Odoo
1. User Access Control

• Create groups ➝ assign users to groups.
• Define roles ➝ Admin, Manager, User, Read-only.

2. Menu & View Restrictions

• Hide menus ➝ restrict visibility by groups.
• Hide views ➝ list / form / kanban / tree by groups.
• Disable developer mode ➝ prevent debug access.

3. Import & Export Control

• Hide Import ➝ restrict for non-admin users.
• Hide Export ➝ allow only for authorized groups.

4. Access Rights on Models

• CRUD control ➝ create / read / write / delete access.
• Sensitive models ➝ restrict (res.users, ir.model, mail.message).
• Record Rules ➝ filter records with domains (ex: only own records).

5. Logs & Chatter Control

• Disable logs ➝ prevent activity log visibility.
• Hide chatter ➝ remove mail thread panel.
• Read-only chatter ➝ users can see but not edit.
• Disable notes ➝ prevent adding comments/attachments.

6. Field-Level Restrictions

• Invisible fields ➝ hide based on user group.
• Read-only fields ➝ restrict editing for some users.
• Hide tabs ➝ conditionally hide sections with attrs or groups.

7. UI & Action Restrictions

• Hide action buttons ➝ validate / confirm / approve.
• Hide smart buttons ➝ remove related records buttons.
• Disable wizards ➝ restrict advanced popups.

8. Advanced Restrictions

• IP restriction ➝ allow login only from defined IPs.
• Disable duplication ➝ prevent "Duplicate" option.
• Restrict developer tools ➝ hide technical features.

9. Simplified Access Setup

• Role hierarchy ➝ Admin ➝ Manager ➝ User ➝ Read-only.
• Group-level setup ➝ assign permissions once, inherit to users.
• Read-only group ➝ auditors/reviewers can only view data.
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",    
    'App Origin': 'Base',
    'depends': ['base','mail','web'],
    'data': [
        'security/security.xml',
        'security/access_groups.xml',
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'views/ax_unauthorized_access_log_views.xml',
        'views/ax_view_res_config_settings.xml',
        'views/ax_res_users_views.xml',
        'views/ax_access_model_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}
