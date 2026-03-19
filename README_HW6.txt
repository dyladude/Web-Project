Homework 6 notes
================

What this adds:
- Unauthenticated AJAX GET: /api/services/
- Authenticated AJAX POST: /api/services/
- Authenticated AJAX PUT: /api/services/<id>/
- Authenticated AJAX DELETE: /api/services/<id>/
- User management UI on /
- Basic Auth protected user endpoints
- Admin-only credential creation, update, and delete

Admin credentials for grading:
- Create an admin account before demoing:
  python manage.py createsuperuser
- Or in Django shell:
  from django.contrib.auth import get_user_model
  User = get_user_model()
  User.objects.create_user('adminhw6', password='ReplaceThis123!', is_staff=True, is_superuser=True)

Suggested author test account:
  User.objects.create_user('authorhw6', password='ReplaceThis123!')

Rubric behavior:
- Missing/invalid Authorization header on POST/PUT/DELETE returns 401 with WWW-Authenticate.
- Valid non-admin user gets 403 on user create/update/delete.
- HTTPS is still handled by your existing nginx/Let's Encrypt setup.
