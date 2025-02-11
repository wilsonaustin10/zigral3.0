# VDI deployment testing

## Tasks:

- [ ] Inspect container logs for Kasm, orchestrator, and Postgres containers to verify everything is running correctly and note any architecture-related issues. Consider adding flags for the correct architecture if needed.
- [ ] Update docker-compose.vdi.yml with appropriate platform flags (e.g., for Kasm container) to work on linux/arm64 if necessary.
- [ ] Setup Kasm free tier subscription and update the .env file with required API credentials and configurations.
- [ ] Test the deployment by accessing http://localhost:6901 (Kasm web interface) and http://localhost:8080/dashboard.
- [ ] Once deployment is verified, build the frontend UI for the dashboard to test functionality. 