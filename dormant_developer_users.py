import os
import requests
import time
import csv
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ORG_NAMES = [name.strip() for name in os.getenv("ORG_NAMES", "").split(",") if name.strip()]
DAYS_INACTIVE_THRESHOLD = int(os.getenv('DAYS_INACTIVE_THRESHOLD', '60'))

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v4+json"
}

def run_query(query: str, variables: dict | None = None):
    payload = {"query": query, "variables": variables}
    resp = requests.post("https://api.github.com/graphql", json=payload, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        print("GraphQL Error Response:", data["errors"])
        raise Exception("GraphQL query returned errors.")
    return data

def get_all_org_members_for_org(org: str) -> list[str]:
    members: list[str] = []
    cursor, has_next = None, True
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        membersWithRole(first: 100, after: $cursor) {
          nodes { login }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    while has_next:
        vars = {"org": org, "cursor": cursor}
        data = run_query(query, vars)
        nodes = data["data"]["organization"]["membersWithRole"]["nodes"]
        members.extend(node["login"] for node in nodes)
        page = data["data"]["organization"]["membersWithRole"]["pageInfo"]
        cursor, has_next = page["endCursor"], page["hasNextPage"]
    return members

def get_repositories_for_org(org: str) -> list[str]:
    repos, cursor, has_next = [], None, True
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        repositories(first: 100, after: $cursor) {
          nodes { name }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    while has_next:
        data = run_query(query, {"org": org, "cursor": cursor})
        repos.extend(repo["name"] for repo in data["data"]["organization"]["repositories"]["nodes"])
        page = data["data"]["organization"]["repositories"]["pageInfo"]
        cursor, has_next = page["endCursor"], page["hasNextPage"]
    return repos

def get_all_branches(repo: str, org: str) -> list[str]:
    branches, cursor, has_next = [], None, True
    query = """
    query($org: String!, $repo: String!, $cursor: String) {
      repository(owner: $org, name: $repo) {
        refs(refPrefix: \"refs/heads/\", first: 100, after: $cursor) {
          nodes { name }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    while has_next:
        vars = {"org": org, "repo": repo, "cursor": cursor}
        data = run_query(query, vars)
        branches.extend(ref["name"] for ref in data["data"]["repository"]["refs"]["nodes"])
        page = data["data"]["repository"]["refs"]["pageInfo"]
        cursor, has_next = page["endCursor"], page["hasNextPage"]
    return branches

def collect_branch_activity(org: str, repo: str, branch: str, since_iso: str) -> dict[str, str]:
    activity: dict[str, str] = {}

    q_commits = """
    query($owner: String!, $name: String!, $branch: String!, $since: GitTimestamp!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        ref(qualifiedName: $branch) {
          target { ... on Commit { history(first: 100, after: $cursor, since: $since) {
            nodes { author { user { login }, date } }
            pageInfo { hasNextPage endCursor }
          }}}
        }
      }
    }
    """
    cursor, has_next = None, True
    while has_next:
        vars = {"owner": org, "name": repo, "branch": branch, "since": since_iso, "cursor": cursor}
        data = run_query(q_commits, vars)
        ref = data["data"]["repository"].get("ref")
        if not ref or not ref.get("target"): break
        hist = ref["target"]["history"]
        for node in hist["nodes"]:
            user = node["author"].get("user")
            if user:
                login, date = user["login"], node["author"]["date"]
                if login not in activity or activity[login] < date:
                    activity[login] = date
        cursor, has_next = hist["pageInfo"]["endCursor"], hist["pageInfo"]["hasNextPage"]

    q_issues = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        issues(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes { author { login }, updatedAt }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    cursor, has_next = None, True
    while has_next:
        data = run_query(q_issues, {"owner": org, "name": repo, "cursor": cursor})
        for issue in data["data"]["repository"]["issues"]["nodes"]:
            if issue["author"]:
                login, date = issue["author"]["login"], issue["updatedAt"]
                if login not in activity or activity[login] < date:
                    activity[login] = date
        page = data["data"]["repository"]["issues"]["pageInfo"]
        cursor, has_next = page["endCursor"], page["hasNextPage"]

    q_prs = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(states: [OPEN, CLOSED, MERGED], orderBy: {field: UPDATED_AT, direction: DESC}, first: 100, after: $cursor) {
          nodes { author { login }, updatedAt }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    cursor, has_next = None, True
    while has_next:
        data = run_query(q_prs, {"owner": org, "name": repo, "cursor": cursor})
        for pr in data["data"]["repository"]["pullRequests"]["nodes"]:
            if pr["author"]:
                login, date = pr["author"]["login"], pr["updatedAt"]
                if login not in activity or activity[login] < date:
                    activity[login] = date
        page = data["data"]["repository"]["pullRequests"]["pageInfo"]
        cursor, has_next = page["endCursor"], page["hasNextPage"]

    return activity

def main():
    if not ORG_NAMES:
        print("❗ Please set ORG_NAMES in your .env file")
        return

    for ORG_NAME in ORG_NAMES:
        print(f"\n🔍 Fetching repos for organization: {ORG_NAME}")
        try:
            repos = get_repositories_for_org(ORG_NAME)
        except Exception as e:
            print(f"❌ Skipping org {ORG_NAME} due to error: {e}")
            continue

        print(f"📦 Total repositories found in {ORG_NAME}: {len(repos)}")

        since_date = datetime.now(timezone.utc) - timedelta(days=DAYS_INACTIVE_THRESHOLD)
        since_iso = since_date.isoformat()

        overall_activity: dict[str, str] = {}
        repo_counter = 0

        for repo in repos:
            repo_counter += 1
            print(f"\n📁 Repo [{repo_counter}/{len(repos)}]: {repo}")
            try:
                branches = get_all_branches(repo, ORG_NAME)
                if not branches:
                    print("  ⚠️  No branches, skipping.")
                    continue
                for br in branches:
                    print(f"  🔍 Branch: {br}")
                    try:
                        act = collect_branch_activity(ORG_NAME, repo, br, since_iso)
                        for user, date in act.items():
                            if user not in overall_activity or overall_activity[user] < date:
                                overall_activity[user] = date
                    except Exception as e:
                        print(f"  ⚠️  Skipping branch '{br}' due to error: {e}")
            except Exception as e:
                print(f"❌ Error on repo '{repo}': {e}")

            if repo_counter % 100 == 0:
                print("⏳ Sleeping 2 seconds to respect rate limits…")
                time.sleep(2)

        print("\n🔄 Fetching org members for never-active detection…")
        all_members = set(get_all_org_members_for_org(ORG_NAME))
        active_tracked = set(overall_activity.keys())
        never_active_users = all_members - active_tracked

        filename = f"user_activity_report_{ORG_NAME}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        print(f"📄 Writing CSV -> {filename}")

        with open(filename, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["Users", "Last activity", "active"])
            for user, last_iso in overall_activity.items():
                dt = datetime.strptime(last_iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                w.writerow([user, dt.strftime("%d-%m-%Y"), str(dt >= since_date).lower()])
            for user in sorted(never_active_users):
                w.writerow([user, "N/A", "never-active"])

        print(f"✅ Done with {ORG_NAME}")

if __name__ == "__main__":
    main()
