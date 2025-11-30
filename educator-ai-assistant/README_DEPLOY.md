Deployment note:
- 2025-11-30: Added scripts to inspect and dedupe `schedules` table and removed
	duplicate schedule rows locally. DB backups were created but not committed.
	These scripts are in `scripts/` and can be used to recover or clean local
	SQLite databases before deploying. No database files were added to the repo.

