#!/bin/bash
# Switch Paddle between sandbox and production
# Usage: ./switch_paddle_env.sh sandbox|production

ENV_FILE="/opt/evolvixos/.env"
MODE="${1:-production}"

if [ "$MODE" = "sandbox" ]; then
    echo "Switching to SANDBOX mode..."
    # Backup production values
    sed -i "s/^PADDLE_API_KEY=/PADDLE_PROD_API_KEY_BACKUP=/" $ENV_FILE 2>/dev/null
    sed -i "s/^PADDLE_CLIENT_TOKEN=/PADDLE_PROD_CLIENT_TOKEN_BACKUP=/" $ENV_FILE 2>/dev/null
    sed -i "s/^PADDLE_WEBHOOK_SECRET=/PADDLE_PROD_WEBHOOK_SECRET_BACKUP=/" $ENV_FILE 2>/dev/null
    
    # Set sandbox values (replace these with actual sandbox keys)
    sed -i "s/^PADDLE_ENVIRONMENT=.*/PADDLE_ENVIRONMENT=sandbox/" $ENV_FILE
    sed -i "s/^PADDLE_API_BASE=.*/PADDLE_API_BASE=https:\/\/api.paddle.com/" $ENV_FILE
    
    echo "NOTE: You need to set PADDLE_API_KEY and PADDLE_CLIENT_TOKEN"
    echo "      to the sandbox values (pdl_sdbx_... and test_...)"
    echo ""
    echo "Edit $ENV_FILE and set:"
    echo "  PADDLE_API_KEY=pdl_sdbx_apikey_..."
    echo "  PADDLE_CLIENT_TOKEN=test_..."
    echo "  PADDLE_ENVIRONMENT=sandbox"
    
elif [ "$MODE" = "production" ]; then
    echo "Switching to PRODUCTION mode..."
    # Restore production values
    sed -i "s/^PADDLE_PROD_API_KEY_BACKUP=/PADDLE_API_KEY=/" $ENV_FILE 2>/dev/null
    sed -i "s/^PADDLE_PROD_CLIENT_TOKEN_BACKUP=/PADDLE_CLIENT_TOKEN=/" $ENV_FILE 2>/dev/null
    sed -i "s/^PADDLE_PROD_WEBHOOK_SECRET_BACKUP=/PADDLE_WEBHOOK_SECRET=/" $ENV_FILE 2>/dev/null
    
    sed -i "s/^PADDLE_ENVIRONMENT=.*/PADDLE_ENVIRONMENT=production/" $ENV_FILE
    sed -i "s/^PADDLE_API_BASE=.*/PADDLE_API_BASE=https:\/\/api.paddle.com/" $ENV_FILE
    echo "Restored production keys."
else
    echo "Usage: $0 sandbox|production"
    exit 1
fi

# Restart auth service
echo "Restarting auth service..."
systemctl restart evolvixos-auth 2>/dev/null || true
echo "Done. Current Paddle env:"
grep PADDLE_ENVIRONMENT $ENV_FILE
grep PADDLE_API_BASE $ENV_FILE
