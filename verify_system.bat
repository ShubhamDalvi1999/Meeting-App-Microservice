@echo off
echo ===== Meeting App System Verification =====
echo.

echo Step 1: Verifying database connections...
python scripts\verify_db.py
if %ERRORLEVEL% NEQ 0 (
    echo Database verification failed!
    exit /b 1
)

echo.
echo Step 2: Verifying meeting CRUD operations...
python scripts\verify_meeting_crud.py
if %ERRORLEVEL% NEQ 0 (
    echo Meeting CRUD verification failed!
    exit /b 1
)

echo.
echo Step 3: Verifying JWT authentication flow...
python scripts\verify_auth_flow.py
if %ERRORLEVEL% NEQ 0 (
    echo Authentication flow verification failed!
    exit /b 1
)

echo.
echo ===== All verifications passed successfully! =====
exit /b 0 