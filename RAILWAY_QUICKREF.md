# Railway CLI Quick Reference

Essential Railway CLI commands for managing your deployment.

## Setup & Authentication

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize new project
railway init

# Link to existing project
railway link
```

## Deployment

```bash
# Deploy from current directory
railway up

# Deploy with detached mode (don't wait)
railway up --detach

# Deploy specific service
railway up --service <service-name>
```

## Logs & Monitoring

```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs --follow

# Filter logs by time
railway logs --since 1h
railway logs --since 30m

# View status
railway status

# Show metrics
railway metrics
```

## Environment Variables

```bash
# List all variables
railway variables

# Set a variable
railway variables set KEY=value
railway variables set KEY="value with spaces"

# Set multiple variables
railway variables set KEY1=value1 KEY2=value2

# Delete a variable
railway variables delete KEY

# Load variables from .env file
railway variables set $(cat .env)
```

## Domain Management

```bash
# List domains
railway domain

# Add custom domain
railway domain add example.com

# Remove domain
railway domain delete example.com
```

## Volume Management

```bash
# List volumes
railway volume list

# Create volume
railway volume add --mount-path <path>

# Create database volume (for this project)
railway volume add --mount-path /app/instance

# Delete volume (⚠️ DESTRUCTIVE)
railway volume delete <volume-id>
```

## Running Commands

```bash
# Run command in production environment
railway run <command>

# Examples:
railway run python manage.py migrate
railway run flask init-db
railway run bash

# Run command in specific service
railway run --service <service-name> <command>
```

## Project Management

```bash
# Show current project info
railway whoami

# Open project in browser
railway open

# Open Railway dashboard
railway open --dashboard

# Restart service
railway restart

# List services
railway service
```

## Database Operations

```bash
# Connect to database (if PostgreSQL/MySQL)
railway connect

# Run bash in production
railway run bash

# Backup SQLite database
railway run sqlite3 /app/instance/medal_pool.db .dump > backup.sql

# Restore SQLite database
railway run bash -c "sqlite3 /app/instance/medal_pool.db < backup.sql"

# Check database size
railway run du -sh /app/instance/medal_pool.db

# View database content
railway run sqlite3 /app/instance/medal_pool.db "SELECT * FROM contest;"
```

## Rollback & Recovery

```bash
# Rollback to previous deployment
railway rollback

# Rollback to specific deployment
railway rollback <deployment-id>

# List deployments
railway deployments

# View deployment details
railway deployment <deployment-id>
```

## Debugging

```bash
# Check build logs
railway logs --build

# Check deployment logs
railway logs --deployment <deployment-id>

# Run shell in production
railway run bash

# Check environment variables in production
railway run env

# Test connectivity
railway run curl http://localhost:8000

# Check Python version
railway run python --version

# List files in production
railway run ls -la

# Check disk usage
railway run df -h
```

## Common Troubleshooting Commands

```bash
# Database not persisting?
railway volume list
railway run ls -la /app/instance

# Environment variables not loading?
railway variables
railway run env | grep FLASK

# SSL not working?
railway domain
railway status

# App not starting?
railway logs --follow
railway run bash
```

## Project-Specific Commands (OlympicPool2)

```bash
# Initialize database
railway run flask init-db

# Load countries
railway run flask load-countries

# Check contest configuration
railway run sqlite3 /app/instance/medal_pool.db "SELECT * FROM contest;"

# Check users
railway run sqlite3 /app/instance/medal_pool.db "SELECT id, email, name, team_name FROM users;"

# Check picks
railway run sqlite3 /app/instance/medal_pool.db "SELECT user_id, COUNT(*) as picks FROM picks GROUP BY user_id;"

# Backup database
railway run sqlite3 /app/instance/medal_pool.db .dump > backup-$(date +%Y%m%d).sql

# Check application health
railway run curl -f http://localhost:8000 || echo "App not responding"

# View gunicorn workers
railway run ps aux | grep gunicorn
```

## Environment-Specific Commands

```bash
# Production environment
railway environment production
railway logs
railway variables

# Staging environment
railway environment staging
railway logs
railway variables

# Switch back to production
railway environment production
```

## Cost Management

```bash
# View usage metrics
railway metrics

# Check current plan
railway whoami

# Monitor resource usage
railway run free -h
railway run df -h
```

## Git Integration

```bash
# View connected repository
railway status

# Trigger deployment from specific branch
git push origin main  # Auto-deploys if GitHub connected

# Disable auto-deploy
# (Do this in Railway dashboard → Settings → Deploy)

# Manual deploy after disabling auto-deploy
railway up
```

## Tips & Best Practices

### Security
- Never commit `.env` files
- Use Railway variables for secrets
- Rotate secrets periodically
- Use `SESSION_COOKIE_SECURE=True` in production

### Performance
- Monitor logs for errors
- Check memory usage regularly: `railway run free -h`
- Optimize database queries (avoid N+1)
- Use caching where appropriate

### Deployment
- Test locally before deploying
- Use staging environment for testing
- Keep dependencies updated
- Always backup database before major changes

### Monitoring
- Check logs daily: `railway logs`
- Set up alerts (Railway dashboard)
- Monitor disk usage: `railway run df -h`
- Track deployment times

### Database
- Backup regularly (at least weekly)
- Test restore process
- Monitor database size
- Vacuum SQLite periodically: `railway run sqlite3 /app/instance/medal_pool.db "VACUUM;"`

## Emergency Procedures

### App Down
```bash
# 1. Check logs
railway logs --follow

# 2. Check status
railway status

# 3. Restart service
railway restart

# 4. If still down, rollback
railway rollback
```

### Database Corruption
```bash
# 1. Stop accepting traffic (update contest state to 'locked')

# 2. Backup current database
railway run sqlite3 /app/instance/medal_pool.db .dump > emergency-backup.sql

# 3. Restore from last good backup
railway run bash
sqlite3 /app/instance/medal_pool.db < backup-YYYYMMDD.sql
exit

# 4. Restart service
railway restart
```

### Out of Disk Space
```bash
# 1. Check disk usage
railway run df -h

# 2. Check database size
railway run du -sh /app/instance/*

# 3. Vacuum database
railway run sqlite3 /app/instance/medal_pool.db "VACUUM;"

# 4. Check logs size
railway run du -sh /var/log/*

# 5. If needed, upgrade volume size in Railway dashboard
```

## Useful Aliases (Add to ~/.bashrc or ~/.zshrc)

```bash
# Railway shortcuts
alias rl='railway logs --follow'
alias rs='railway status'
alias rv='railway variables'
alias rr='railway restart'
alias ro='railway open'
alias rd='railway run bash'

# OlympicPool2 specific
alias rdb='railway run sqlite3 /app/instance/medal_pool.db'
alias rbackup='railway run sqlite3 /app/instance/medal_pool.db .dump > backup-$(date +%Y%m%d).sql'
```

## Getting Help

```bash
# Railway CLI help
railway help
railway <command> --help

# Railway documentation
# https://docs.railway.app

# Railway Discord
# https://discord.gg/railway

# Check Railway status
# https://status.railway.app
```

## Quick Deployment Checklist

Before deploying:
- [ ] All tests passing locally
- [ ] `.env.example` updated
- [ ] `requirements.txt` updated
- [ ] Database migrations tested
- [ ] Environment variables configured in Railway
- [ ] Volume created and mounted
- [ ] Backup of current database

After deploying:
- [ ] Check logs for errors: `railway logs --follow`
- [ ] Verify app is accessible
- [ ] Test critical user flows
- [ ] Check database persistence
- [ ] Monitor for 10-15 minutes

## Additional Resources

- Railway Documentation: https://docs.railway.app
- Railway GitHub: https://github.com/railwayapp
- Railway Blog: https://blog.railway.app
- Railway Community: https://community.railway.app

---

**Last Updated:** 2026-01-26
**Version:** 1.0
