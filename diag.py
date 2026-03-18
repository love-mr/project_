import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'childvaccination_project.settings'
with open('diag_out.txt', 'w', encoding='utf-8') as f:
    try:
        import django
        django.setup()
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('seed_data', stdout=out)
        f.write(out.getvalue() + '\n')
        f.write('=== SEED DONE ===\n')
    except Exception as e:
        import traceback
        traceback.print_exc(file=f)
