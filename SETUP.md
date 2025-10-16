# ABE Portal - Setup Anleitung

## Nach dem Deployment

1. **PostgreSQL Extensions manuell erstellen:**
```bash
# In Portainer: Backend Container → Console
docker exec -it abe-portal-backend bash

# Extensions erstellen
PGPASSWORD=secure_password_change_me psql -h db -U abeportal -d abeportal -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
PGPASSWORD=secure_password_change_me psql -h db -U abeportal -d abeportal -c "CREATE EXTENSION IF NOT EXISTS unaccent;"

# Migration ausführen
alembic upgrade head
```

2. **Admin-Benutzer erstellen:**
```bash
# Im Backend Container
python -c "
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.auth import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    password_hash=get_password_hash('admin123'),
    role=UserRole.ADMIN,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created: admin/admin123')
"
```

3. **Portal testen:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/health
- Login: admin / admin123
