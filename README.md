# On Call Records

A Django-based system for managing on-call staff schedules, time tracking, and bank holiday management.

## Bank Holiday Management

The system automatically tracks UK bank holidays to properly categorize work days and calculate appropriate claims. Bank holidays are used throughout the system to determine day types and payment rates.

### For System Administrators

#### Managing Bank Holidays via Admin Panel

1. **Access the Admin Panel**
   - Go to your Django admin interface (usually `/admin/`)
   - Navigate to "Records" → "Bank Holidays"

2. **Viewing Current Bank Holidays**
   - You'll see a list of all bank holidays in the system
   - Use the date filter to find specific years or periods
   - Search by holiday name (e.g., "Christmas", "Easter")

3. **Importing Bank Holidays**
   
   The system provides three ways to import bank holiday data:

   **Option 1: Automatic Import (Recommended)**
   - Select any holidays in the list (or none)
   - Choose "Sync bank holidays (auto: cached file first, then API fallback)" from the Actions dropdown
   - Click "Go"
   - This will first try to use the comprehensive local data (2012-2027), then fall back to the UK Government API if needed

   **Option 2: Import from Local File**
   - Select "Sync bank holidays from cached file (2012-2027)" from Actions
   - Click "Go"
   - This imports from a comprehensive local file covering 2012-2027
   - **Advantage**: Very fast and includes historical data
   - **Best for**: Complete setup or historical data needs

   **Option 3: Import from Government API**
   - Select "Sync bank holidays from UK Government API (latest 3 years)" from Actions
   - Click "Go"
   - This fetches the latest data directly from gov.uk
   - **Advantage**: Always has the most current information
   - **Best for**: Getting the very latest holiday announcements

#### When to Import Bank Holidays

- **Initial Setup**: Use "Auto" or "Local file" option to get comprehensive coverage
- **Regular Updates**: The system has historical data through 2027, so you typically won't need to update often
- **New Holidays Announced**: If the government announces new holidays beyond 2027, use the "API" option
- **After System Restore**: Use "Auto" option to restore all bank holiday data

#### Understanding the Results

After importing, you'll see a success message like:
- `Successfully synced 132 bank holidays from local cached file. Created: 50, Updated: 82`

This means:
- **132 holidays** were processed
- **50 new holidays** were added to your system
- **82 existing holidays** were updated with any changes
- **Source**: Shows where the data came from (local file or API)

#### Troubleshooting

**"Failed to sync" Error Messages:**
- **Local file not found**: The cached file might be missing - try "Auto" mode instead
- **API request failed**: Internet connection issue - the local file option should still work
- **No data for region**: Make sure you're using the correct region (England & Wales is default)

**What Regions Are Available:**
- **England and Wales**: Default option, covers most of the UK
- **Scotland**: Includes Scottish-specific holidays like St. Andrew's Day
- **Northern Ireland**: Includes Northern Ireland-specific holidays

#### Command Line Usage (For Technical Users)

If you have command line access, you can also import holidays using:

```bash
# Recommended: Auto mode (tries local file first, then API)
python manage.py sync_bank_holidays

# Import from local file only (2012-2027 data)
python manage.py sync_bank_holidays --source=local

# Import from UK Government API only
python manage.py sync_bank_holidays --source=api

# Import Scottish holidays
python manage.py sync_bank_holidays --region=scotland

# See all available options
python manage.py sync_bank_holidays --help
```

#### Data Coverage

- **Local Cached File**: 2012-2027 (comprehensive historical data)
- **UK Government API**: Last year + next 2 years (always current)
- **Combined Coverage**: Complete from 2012 through at least 2027

### How Bank Holidays Affect the System

1. **Rota Calendar**: Bank holidays are highlighted and affect scheduling
2. **Time Tracking**: Bank holiday hours may have different payment rates
3. **Day Types**: Automatically categorizes days as Weekday/Saturday/Sunday/Bank Holiday
4. **Reports**: Bank holiday hours are tracked separately in monthly reports

### Frequency of Updates

- **Normal Operations**: Bank holidays are stable through 2027 - no regular updates needed
- **Special Occasions**: Government may announce additional holidays (Royal events, state occasions)
- **After 2027**: Will need to import new data from the API or updated local files

TODO: 
    - on call stats
        - rota stats
        - call stats