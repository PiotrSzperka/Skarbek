# Changelog - Forced Password Change Feature

## Date: 2025-11-07

### ✨ New Feature: Forced Password Change on First Login

Parents are now required to change their temporary password when logging in for the first time, improving security.

---

## 📋 Summary

### Backend Changes

#### Database Schema
- Added `force_password_change` (boolean, default `TRUE`) to `parent` table
- Added `password_changed_at` (timestamp with timezone, nullable) to `parent` table
- Created migration system with audit table `schema_migrations`

#### Migration System
- **New file**: `backend/run_migrations.py` - Python script for automated migration execution
- **New file**: `backend/migrations/000_init_migration_system.sql` - Creates audit table
- **New file**: `backend/migrations/001_add_force_password_change.sql` - Adds password change fields
- **New file**: `backend/migrations/README.md` - Migration system documentation
- Features:
  - SHA256 checksums for migration integrity
  - Duplicate execution prevention
  - Transaction rollback on errors
  - Execution timing metrics

#### API Changes
- `POST /api/admin/parents` - Sets `force_password_change=True` on creation
- `POST /api/parents/login` - Returns `require_password_change: true` when flag is set
- `POST /api/parents/change-password-initial` - New endpoint for password change
  - Validates old password
  - Updates password hash
  - Clears `force_password_change` flag
  - Sets `password_changed_at` timestamp
  - Returns new JWT token
- Protected endpoints (`/parents/me`, `/parents/campaigns`, `/parents/contributions`):
  - Return 403 with `password_change_required` code when flag is active

#### Backend Tests
- **New file**: `backend/tests/test_force_password_change.py`
- 9 pytest scenarios covering full flow
- All tests passing ✅

---

### Frontend Changes

#### New Components
- **New file**: `frontend/src/ParentForcePasswordChange.jsx`
  - Password change form with validation
  - Client-side checks: min 6 chars, old ≠ new, confirmation match
  - Error display for API failures

#### Updated Components
- `frontend/src/ParentLogin.jsx`:
  - Checks `require_password_change` flag in login response
  - Redirects to `#/parent/change-password` when flag is set
- `frontend/src/App.jsx`:
  - Added `parent_change_password` route
  - Renders `ParentForcePasswordChange` component

#### API Helpers
- `frontend/src/api.js`:
  - Added `parentChangePasswordInitial(oldPassword, newPassword, token)` function

#### Frontend Tests
- **New file**: `frontend/tests/playwright/parent-force-password-change.spec.ts`
- 3 Playwright e2e scenarios:
  1. Full flow: create → login → change password → logout → login with new password
  2. Guard enforcement: blocked access before change, allowed after
  3. Form validation: short password, same as old, mismatch, wrong old password
- All tests passing ✅

---

### Infrastructure Changes

#### Docker
- `backend/Dockerfile`:
  - Added `COPY ./migrations ./migrations`
  - Added `COPY run_migrations.py .`
  - Ensures migration files are available in container

#### CI/CD Pipeline
- `.github/workflows/cd.yml`:
  - Added "Run database migrations" step after deployment
  - Executes `docker compose exec -T backend python run_migrations.py`
  - Ensures database schema is always up-to-date on deployment

#### Documentation
- **Updated**: `docs/proxmox-deployment.md`
  - Added note about automatic migration execution in CD workflow
- **New**: `backend/migrations/README.md`
  - Comprehensive migration system guide
  - Usage examples, safety features, diagnostic queries
- **New**: `docs/parents-force-password-change.md` (Polish)
  - Complete feature specification
  - Data model, API changes, frontend changes
  - Test scenarios and implementation plan

---

## 🧪 Test Results

### Backend (pytest)
```
9 passed, 1 warning in 1.16s
```

Scenarios:
- ✅ Parent creation sets force_password_change=True
- ✅ Login with flag returns require_password_change
- ✅ Protected endpoints blocked (403)
- ✅ Password change clears flag and sets timestamp
- ✅ Login after change doesn't require change
- ✅ Protected endpoints accessible after change
- ✅ Wrong old password rejected (401)
- ✅ Unauthenticated change rejected

### Frontend (Playwright)
```
3 passed in 8.0s
```

Scenarios:
- ✅ Complete user flow (create → login → change → logout → login)
- ✅ API guard enforcement before/after password change
- ✅ Form validation (length, uniqueness, match, authentication)

---

## 🔒 Security Improvements

1. **Mandatory password change**: Admins create parents with temporary passwords that must be changed
2. **Access control**: Protected resources blocked until password changed
3. **Password policy**: Minimum 6 characters, must differ from old password
4. **Audit trail**: `password_changed_at` timestamp for tracking
5. **Token refresh**: New JWT issued after password change

---

## 📦 Files Changed

### Added (17 files)
- `backend/run_migrations.py`
- `backend/migrations/000_init_migration_system.sql`
- `backend/migrations/001_add_force_password_change.sql`
- `backend/migrations/README.md`
- `backend/tests/test_force_password_change.py`
- `frontend/src/ParentForcePasswordChange.jsx`
- `frontend/tests/playwright/parent-force-password-change.spec.ts`
- `docs/parents-force-password-change.md`
- `CHANGELOG-force-password-change.md` (this file)

### Modified (6 files)
- `backend/app/models.py` - Added fields to Parent model
- `backend/app/api/parents.py` - Added endpoints and guards
- `backend/Dockerfile` - Copy migrations and script
- `frontend/src/ParentLogin.jsx` - Redirect logic
- `frontend/src/App.jsx` - Route handling
- `frontend/src/api.js` - API helper
- `.github/workflows/cd.yml` - Migration execution step
- `docs/proxmox-deployment.md` - CD workflow notes

---

## 🚀 Deployment

### Manual Migration
```bash
docker compose exec backend python run_migrations.py
```

### Automatic (via CD pipeline)
Migrations run automatically after each deployment via GitHub Actions.

---

## 📚 References

- Feature spec: `docs/parents-force-password-change.md`
- Migration guide: `backend/migrations/README.md`
- Deployment guide: `docs/proxmox-deployment.md`
