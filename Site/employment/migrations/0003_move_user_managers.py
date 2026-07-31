from django.db import migrations


def move_managers_to_employees(apps, schema_editor):
    user_model = apps.get_model("users", "FreyjaUser")
    employee_model = apps.get_model("employment", "Employee")

    employees_by_user_id = {}
    for user_id in user_model.objects.values_list("id", flat=True):
        employee, _ = employee_model.objects.get_or_create(user_id=user_id)
        employees_by_user_id[user_id] = employee

    employees_to_update = []
    for user_id, manager_id in user_model.objects.exclude(manager_id=None).values_list(
        "id", "manager_id"
    ):
        employee = employees_by_user_id[user_id]
        employee.manager_id = employees_by_user_id[manager_id].id
        employees_to_update.append(employee)

    if employees_to_update:
        employee_model.objects.bulk_update(employees_to_update, ("manager",))


def restore_managers_to_users(apps, schema_editor):
    user_model = apps.get_model("users", "FreyjaUser")
    employee_model = apps.get_model("employment", "Employee")

    for employee in employee_model.objects.exclude(manager_id=None).select_related("manager"):
        user_model.objects.filter(id=employee.user_id).update(manager_id=employee.manager.user_id)


class Migration(migrations.Migration):
    dependencies = [
        ("employment", "0002_employee_manager"),
    ]

    operations = [
        migrations.RunPython(move_managers_to_employees, restore_managers_to_users),
    ]
