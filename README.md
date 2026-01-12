# GitHub Dormant Developer Users Report

GitHub already provides basic dormant user visibility at the platform level.
This action extends that capability by identifying Dormant Developer Users based on actual development activity—commits, issues, and pull requests—across all repositories.
The resulting report can be downloaded directly from the GitHub Actions workflow.

> Dormant developer users are organization members who have not made commits, opened issues, or created pull requests within a defined time period.

This project is available both as:
- ✅ **A GitHub Action**
- 🐍 **A standalone Python script (optional local usage)**

---

## 🚀 GitHub Action (Marketplace)

Run dormant developer user audits automatically using **GitHub Actions**, without local setup.


## How It Works

- Retrieves all repositories and branches for the configured GitHub organization.
- Collects user activity from commits, issues, and pull requests.
- Determines each user’s most recent activity date across the organization.
- Classifies users as:
  - `active=true` if activity is within the configured inactivity threshold
  - `active=false` if activity exceeds the threshold
  - `never-active`: user is an organization member with no detected commits, issues, or pull requests

- Generates a CSV report summarizing user activity status.


## Usage

```yml
  - name: Run Dormant Developer Users Report
    uses: CanarysAutomations/Dormant-Developer-Users@v1
    with:
      github_token: ${{ secrets.ORG_AUDIT_TOKEN }}
      org_names: org
      days_inactive_threshold: 90


# Uploads the CSV report of dormant developer users so it can be downloaded
  - name: Upload dormant developer users report
    uses: actions/upload-artifact@v4
    with:
      name: dormant-developer-users-report
      path: "*.csv"
```

> ⚠️ **Important:**  
> The GitHub Marketplace installation snippet does not include secret values.  
> You must create a GitHub secret (for example, `ORG_AUDIT_TOKEN`) and explicitly pass it to the action as shown below:
>
> ```yaml
> github_token: ${{ secrets.ORG_AUDIT_TOKEN }}
> ```



### Example workflow

```yaml
name: Dormant Developer Users Audit

on:
  schedule:
    - cron: "0 0 31 2 *"
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Run Dormant Developer Users Report
        uses: CanarysAutomations/Dormant-Developer-Users@v1
        with:
          github_token: ${{ secrets.ORG_AUDIT_TOKEN }}
          org_names: org
          days_inactive_threshold: 90

      - name: Upload dormant developer users report
        uses: actions/upload-artifact@v4
        with:
          name: dormant-developer-users-report
          path: "*.csv"

```

## 🔐 Required Token Permissions

The token used with this action must have the following scopes:

- `read:org – to list organization members`
- `repo - required only if the organization contains private repositories`


## 🔧 GitHub Action Inputs

| Name | Required | Default | Description |
|---|---|---|---|
| `github_token` | Yes | – | GitHub token with `read:org` and repository read access |
| `org_names` | Yes | – | Comma-separated GitHub organization names |
| `days_inactive_threshold` | No | `60` | Days to consider a user inactive |

**Note:**
`days_inactive_threshold` specifies the number of days without developer activity (commits, issues, or pull requests) after which a user is marked as Inactive. If not provided, the default value of 60 days is used.

## Sample Output

| Users                     | Last Activity | Active |
|---------------------------|---------------|--------|
| dependabot                | 14-04-2025    | false  |
| sriplayground             | 24-01-2025    | false  |
| vaishnavn02               | 24-01-2025    | false  |
| Grenston                  | 19-01-2021    | false  |
| balajisriramdas           | 31-12-2025    | true   |
| HarishjKumar-canarys      | 24-01-2025    | false  |
| srionland                 | 30-10-2024    | false  |
| naveen-kunder             | 31-12-2025    | true   |
| akshay-canarys            |	N/A	          | never-active |



## 🐍 Standalone Python Script (Optional Local Usage)

## Overview

The script tracks user activity including:
- Commits to branches
- Issue creation and updates
- Pull request creation and updates

It generates a CSV report showing each user's contribution activity date and whether they're active, inactive, or have never been active.

## Prerequisites

- Python 3.7+
- GitHub Personal Access Token with permissions:
  - `read:org` (read organization data)
  - `repo` (read repository data)

## Installation

Install required packages:

```bash
pip install requests python-dotenv
```

## Configuration

Create a `.env` file with your settings:

```env
GITHUB_TOKEN=your_github_personal_access_token
ORG_NAMES=org1,org2,org3
DAYS_INACTIVE_THRESHOLD=60
```

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required | `ghp_xxxxx` |
| `ORG_NAMES` | Comma-separated list of organizations | Required | `myorg,anotherorg` |
| `DAYS_INACTIVE_THRESHOLD` | Days to consider user inactive | `60` | `90` |

**Note:**
`days_inactive_threshold` specifies the number of days without developer activity (commits, issues, or pull requests) after which a user is marked as Inactive. If not provided, the default value of 60 days is used.

## Usage

Run the script:

```bash
python dormant_developer_users.py
```

## Output

### Console Progress

The script displays real-time progress:

```
🔍 Fetching repos for organization: myorg
📦 Total repositories found in myorg: 145

📁 Repo [1/145]: backend-api
  🔍 Branch: main
  🔍 Branch: develop
📁 Repo [2/145]: frontend-ui
  🔍 Branch: main
  ⚠️  No branches, skipping.
...
⏳ Sleeping 2 seconds to respect rate limits…
...
🔄 Fetching org members for never-active detection…
📄 Writing CSV -> user_activity_report_myorg_20241124_153045.csv
✅ Done with myorg
```

### CSV Report: `user_activity_report_[ORG]_[TIMESTAMP].csv`

Generated report includes:

```csv
Users,Last Activity,active
john-doe,24-11-15,true
jane-smith,24-10-10,false
bob-jones,24-11-20,true
alice-inactive,24-08-01,false
new-user,N/A,never-active
```

#### CSV Columns

| Column | Description | Values |
|--------|-------------|--------|
| `Users` | GitHub username | `username` |
| `Last Activity` | Date of last activity (DD-MM-YY) | `15-11-24` or `N/A` |
| `active` | Activity status | `true`, `false`, or `never-active` |

### Activity Status

- **`true`**: User has activity within the threshold period (default: 60 days)
- **`false`**: User has activity but it's older than the threshold
- **`never-active`**: User is an org member but has no tracked activity

## Features

- ✅ Multi-organization support (process multiple orgs in one run)
- 🔍 Comprehensive activity tracking (commits, issues, PRs)
- 🌿 Scans all branches in all repositories
- 👥 Identifies never-active organization members
- 📊 Timestamped CSV reports for each organization
- 🔄 Built-in rate limit protection
- ⏸️ Periodic delays to avoid API throttling
- 📈 Real-time progress feedback

## How It Works

1. **Load Configuration**: Reads token, organizations, and threshold from `.env`
2. **For Each Organization**:
   - Fetches all repositories using GraphQL API
   - For each repository:
     - Gets all branches
     - For each branch:
       - Collects commits since threshold date
       - Collects issue activity
       - Collects PR activity
     - Tracks the most recent activity per user
   - Fetches all organization members
   - Identifies members with no tracked activity
3. **Generate Report**: Creates CSV with activity status for each user
4. **Rate Limiting**: Adds delays every 100 repositories

## Activity Tracking Details

### Commits
- Tracks commits on all branches
- Uses commit author date
- Only counts commits since threshold date

### Issues
- Tracks issue creation and updates
- Uses `updatedAt` timestamp
- Includes all issue activity

### Pull Requests
- Tracks PRs (open, closed, merged)
- Uses `updatedAt` timestamp
- Includes all PR activity

## Performance Considerations

- **Large Organizations**: Processing can take significant time for orgs with many repos
- **Rate Limits**: Script includes built-in delays (2 seconds per 100 repos)
- **GraphQL API**: Uses GraphQL for efficient bulk data retrieval
- **Pagination**: Automatically handles paginated results

## Use Cases

- 📊 **License Auditing**: Identify inactive users consuming licenses
- 🔐 **Security Review**: Find accounts that haven't been used recently
- 👥 **User Management**: Determine which accounts can be offboarded
- 📈 **Activity Metrics**: Track organization engagement levels
- 💰 **Cost Optimization**: Reclaim licenses from dormant accounts

## Customizing Thresholds

Adjust the inactivity threshold based on your needs:

```env
# 30 days (1 month)
DAYS_INACTIVE_THRESHOLD=30

# 90 days (3 months)
DAYS_INACTIVE_THRESHOLD=90

# 180 days (6 months)
DAYS_INACTIVE_THRESHOLD=180

# 365 days (1 year)
DAYS_INACTIVE_THRESHOLD=365
```

## Processing Multiple Organizations

Process multiple organizations in one run:

```env
ORG_NAMES=org1,org2,org3,org4
```

Each organization gets its own timestamped CSV report.

## Troubleshooting

### "Please set ORG_NAMES in your .env file"
Add `ORG_NAMES` to your `.env` file with at least one organization.

### "GraphQL query returned errors"
- Verify your token has the correct permissions (`read:org`, `repo`)
- Check that organization names are spelled correctly
- Ensure you have access to the organizations

### Rate Limit Issues
The script includes automatic rate limit handling, but if you encounter issues:
- Increase the sleep duration in the code
- Process fewer organizations at once
- Use a GitHub App token (higher rate limits)

### Slow Performance
For organizations with many repositories:
- Run during off-peak hours
- Process one organization at a time
- Consider filtering repositories if possible

### "Skipping branch due to error"
- Empty branches or protected branches may cause errors
- The script continues processing other branches
- Check specific error messages for details

## Interpreting Results

### High Percentage of Inactive Users
- Review onboarding/offboarding processes
- Consider implementing automatic account reviews
- Verify threshold is appropriate for your organization

### Users Marked "never-active"
- May be recently added members
- Could be accounts waiting for project assignment
- Might be external collaborators with limited access
- Consider manual review for these accounts

### All Users Showing as Active
- Threshold might be too long
- Organization may be highly engaged
- Verify script is scanning all repositories

## Best Practices

- 🔄 **Run Regularly**: Schedule monthly or quarterly reports
- 📊 **Track Trends**: Compare reports over time
- 👥 **Review Before Action**: Manually verify before removing access
- 📝 **Document Policy**: Define clear inactivity policies
- 🔐 **Secure Output**: CSV files contain user lists - handle securely
- ⏰ **Off-Peak Runs**: Run during low-usage periods to reduce impact

## Limitations

- **Activity Types**: Only tracks commits, issues, and PRs (not code reviews, comments, reactions)
- **API Visibility**: Can only see activity in accessible repositories
- **Private Activity**: Private contributions may not be fully tracked
- **Historical Data**: GraphQL history queries may have limitations
- **Deleted Content**: Activity on deleted branches/repos not tracked


## Additional Resources

- [GitHub GraphQL API Documentation](https://docs.github.com/en/graphql)
- [GitHub API Rate Limits](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [Organization Member Management](https://docs.github.com/en/organizations/managing-membership-in-your-organization)
- [GitHub Activity Overview](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/managing-contribution-settings-on-your-profile/viewing-contributions-on-your-profile)
