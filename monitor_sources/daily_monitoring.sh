#!/bin/bash

# Comprehensive Daily Monitoring Script
# Checks MongoDB backup files and CSV row counts
# Usage: ./daily_monitoring.sh [YYYY_MM_DD] [--no-email]

# Sending email using mutt with kchou's email configuration
# Changing ~/.mutt/muttrc to use another's email settings
# Making a new gpg key by echo echo "app password" | gpg --encrypt --armor -r key_name > ~/.mutt/your_key_file.gpg
# Modifying ~/.mutt/get-password-gpg.sh
# Write to crontab with running this in terminal (crontab -l 2>/dev/null; echo "0 8 * * * cd /home/acdc/telemetry_webpage/monitor_sources && ./daily_monitoring.sh") | crontab -

# Parse command line arguments
SEND_EMAIL=true
for arg in "$@"; do
    case $arg in
        --no-email)
            SEND_EMAIL=false
            shift
            ;;
        *)
            # If it's not --no-email, assume it's the date argument
            if [[ "$arg" =~ ^[0-9]{4}_[0-9]{2}_[0-9]{2}$ ]]; then
                DATE_ARG="$arg"
            fi
            ;;
    esac
done

# Get today's date
if [[ -n "$DATE_ARG" ]]; then
    TODAY="$DATE_ARG"
else
    TODAY=$(date +"%Y_%m_%d")
fi

# Email configuration
EMAIL_LIST_FILE="./email_list.txt"

# Email flags
EMAIL_NEEDED=false

# Function to read email list
read_email_list() {
    if [ -f "$EMAIL_LIST_FILE" ]; then
        # Read emails, skip comments and empty lines
        grep -v '^#' "$EMAIL_LIST_FILE" | grep -v '^$' | tr '\n' ',' | sed 's/,$//'
    else
        echo "soft_acdc@asiaa.sinica.edu.tw"  # Default fallback
    fi
}

# Function to send email alerts
send_warning_email() {
    local subject="$1"
    local reason="$2"
    
    if [ "$SEND_EMAIL" = true ]; then
        EMAIL_BODY="$reason"
        EMAIL_LIST=$(read_email_list)
        
        echo "$EMAIL_BODY" | mutt -s "$subject" "$EMAIL_LIST"
        echo "📧 Email sent to: $EMAIL_LIST"
    else
        echo "📧 Email disabled - would have sent: $subject"
    fi
}

#################################
# MongoDB Backup Check
#################################

# Define the backup directory and filename
BACKUP_DIR="/var/www/telemetry"
BACKUP_FILE="mongo_backup_${TODAY}.tar.gz"
FULL_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Check if the backup file exists
if [ -f "$FULL_PATH" ]; then
    echo "✓ Backup file found: $FULL_PATH"
    # Show file details
    BACKUP_MOD=$(stat -c "%y" "$FULL_PATH" 2>/dev/null || stat -f "%Sm" "$FULL_PATH" 2>/dev/null || echo "Unknown")
    echo "   Modified: $BACKUP_MOD"
    BACKUP_STATUS="✓ FOUND"
else
    echo "✗ Backup file NOT found: $FULL_PATH"
    echo "Checking directory contents:"
    if [ -d "$BACKUP_DIR" ]; then
        echo "Recent backup files in $BACKUP_DIR:"
        ls -la "$BACKUP_DIR" | grep mongo_backup | tail -5
    else
        echo "Directory $BACKUP_DIR does not exist"
    fi
    BACKUP_STATUS="✗ NOT FOUND"
    EMAIL_NEEDED=true
fi

echo

#################################
# CSV Files Check
#################################

# Define the data directory
DATA_DIR="../processed_data"

# Check if directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Directory $DATA_DIR does not exist"
    CSV_STATUS="✗ DIRECTORY NOT FOUND"
else
    # Function to count rows (excluding header)
    count_rows() {
        local file=$1
        if [ -f "$file" ]; then
            # Count total lines and subtract 1 for header
            local total_lines=$(wc -l < "$file")
            local data_rows=$((total_lines - 1))
            echo "$data_rows"
        else
            echo "FILE NOT FOUND"
        fi
    }

    # Check processed_entries.csv
    echo "📄 processed_entries.csv"
    ENTRIES_FILE="$DATA_DIR/processed_entries.csv"
    ENTRIES_ROWS=$(count_rows "$ENTRIES_FILE")

    # Check processed_sessions.csv
    echo "📄 processed_sessions.csv"
    SESSIONS_FILE="$DATA_DIR/processed_sessions.csv"
    SESSIONS_ROWS=$(count_rows "$SESSIONS_FILE")

    # Compare with yesterday's counts
    if [ -f "./daily_row_counts.txt" ]; then
        LAST_COUNT=$(tail -n 1 "./daily_row_counts.txt")
        LAST_ENTRIES=$(echo "$LAST_COUNT" | awk '{print $2}')
        LAST_SESSIONS=$(echo "$LAST_COUNT" | awk '{print $3}')
        if [[ "$ENTRIES_ROWS" -gt 0 && "$SESSIONS_ROWS" -gt 0 && "$LAST_ENTRIES" -gt 0 && "$LAST_SESSIONS" -gt 0 ]]; then
            if [[ "$ENTRIES_ROWS" -gt "$LAST_ENTRIES" && "$SESSIONS_ROWS" -gt "$LAST_SESSIONS" ]]; then
                echo "📈 Entries and Sessions increased compared to yesterday."
                CHANGE_STATUS="📈 INCREASED"
            else
                echo "📊 Count unchanged or decreased compared to yesterday."
                CHANGE_STATUS="📊 UNCHANGED/DECREASED"
                EMAIL_NEEDED=true
            fi
        else
            echo "⚠️  Cannot compare with yesterday's counts: one or both files are missing or empty."
            CHANGE_STATUS="⚠️  NO COMPARISON"
            EMAIL_NEEDED=true
        fi
    else
        echo "⚠️  No previous counts found for comparison."
        CHANGE_STATUS="⚠️  NO HISTORY"
    fi

    # Output the row counts to the file
    if [[ "$ENTRIES_ROWS" != "FILE NOT FOUND" && "$SESSIONS_ROWS" != "FILE NOT FOUND" && "$SESSIONS_ROWS" -gt 0 ]]; then
        echo "$TODAY $ENTRIES_ROWS $SESSIONS_ROWS" >> "./daily_row_counts.txt"
        echo "✓ Row counts logged to daily_row_counts.txt"
        CSV_STATUS="✓ FILES OK"
    else
        echo "✗ Cannot output row counts: one or both files are missing or empty."
        CSV_STATUS="✗ FILES MISSING/EMPTY"
    fi
fi

echo

#################################
# Summary Report
#################################
echo "📋 Summary Report"
echo "================="
echo "Date: $TODAY"
echo "MongoDB Backup: $BACKUP_STATUS"
echo "CSV Files: $CSV_STATUS"
if [[ "$ENTRIES_ROWS" != "FILE NOT FOUND" && "$SESSIONS_ROWS" != "FILE NOT FOUND" ]]; then
    if [[ -n "$CHANGE_STATUS" ]]; then
        echo "Data change: $CHANGE_STATUS"
    fi
fi
echo

#################################
# Send Email Alerts
#################################

# Send consolidated email if any issues detected
if [ "$EMAIL_NEEDED" = true ]; then
    EMAIL_SUBJECT="ALERT: Telemetry Monitoring Issues - $TODAY"
    EMAIL_BODY="TELEMETRY MONITORING ALERT for $TODAY

Summary:
- MongoDB Backup: $BACKUP_STATUS
- Data change: $CHANGE_STATUS

Please check the telemetry system and resolve any issues."

    send_warning_email "$EMAIL_SUBJECT" "$EMAIL_BODY"
fi

echo

# Exit with appropriate code
if [[ "$BACKUP_STATUS" == *"FOUND"* && "$CSV_STATUS" == *"OK"* ]]; then
    echo "✅ All checks passed"
    exit 0
else
    echo "❌ Some checks failed"
    exit 1
fi
