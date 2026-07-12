"""GitHub API client wrapper.

Uses both REST and GraphQL APIs to fetch user stats.
"""

from typing import Dict, Any, List
import requests
from scripts.utils import logger

class GitHubAPI:
    """Wrapper class for GitHub REST and GraphQL APIs."""
    
    def __init__(self, token: str):
        """Initializes the API client with a GitHub token."""
        if not token:
            raise ValueError("GH_TOKEN is missing or empty")
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Antigravity-Updater"
        }

    def _get_rest(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Makes a GET request to the GitHub REST API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"REST GET: {url} with params {params}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _post_graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Makes a POST request to the GitHub GraphQL API."""
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Antigravity-Updater"
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        logger.debug(f"GraphQL POST to {url}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        return data

    def get_search_count(self, q: str) -> int:
        """Helper to get total_count from search endpoints (commits, issues, PRs)."""
        # REST Search API
        res = self._get_rest("search/issues", params={"q": q, "per_page": 1})
        return res.get("total_count", 0)

    def get_total_commits_rest(self, username: str) -> int:
        """Retrieves lifetime commits count using search API."""
        # Using search/commits API
        url = f"{self.base_url}/search/commits"
        params = {"q": f"author:{username}", "per_page": 1}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("total_count", 0)

    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Queries the GraphQL API for user profile, followers, calendar, and owned repos.
        
        Paginates repositories if there are more than 100.
        """
        repos = []
        cursor = None
        has_next = True
        followers_count = 0
        calendar_contributions = 0
        contributed_to_count = 0
        
        while has_next:
            query = """
            query($login: String!, $cursor: String) {
              user(login: $login) {
                followers {
                  totalCount
                }
                contributionsCollection {
                  contributionCalendar {
                    totalContributions
                  }
                }
                repositoriesContributedTo(contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW]) {
                  totalCount
                }
                repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false) {
                  totalCount
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  nodes {
                    name
                    stargazerCount
                    createdAt
                    pushedAt
                    cloneUrl
                    isPrivate
                  }
                }
              }
            }
            """
            variables = {"login": username, "cursor": cursor}
            res = self._post_graphql(query, variables)
            user_data = res.get("data", {}).get("user")
            if not user_data:
                raise Exception(f"User {username} not found in GraphQL response")
            
            followers_count = user_data.get("followers", {}).get("totalCount", 0)
            calendar_contributions = user_data.get("contributionsCollection", {}).get("contributionCalendar", {}).get("totalContributions", 0)
            contributed_to_count = user_data.get("repositoriesContributedTo", {}).get("totalCount", 0)
            
            repo_conn = user_data.get("repositories", {})
            nodes = repo_conn.get("nodes", [])
            repos.extend(nodes)
            
            page_info = repo_conn.get("pageInfo", {})
            has_next = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

        # Sort by creation date to find latest repo
        sorted_repos = sorted(repos, key=lambda r: r.get("createdAt", ""), reverse=True)
        latest_repo = sorted_repos[0]["name"] if sorted_repos else "N/A"
        
        # Calculate total stars
        total_stars = sum(r.get("stargazerCount", 0) for r in repos)
        
        # Fetch PRs and Issues count via REST search API (lifetime)
        total_prs = self.get_search_count(f"author:{username} type:pr")
        total_issues = self.get_search_count(f"author:{username} type:issue")
        
        # Fetch commits count via REST search API (lifetime)
        total_commits = self.get_total_commits_rest(username)

        return {
            "repository_count": len(repos),
            "total_stars": total_stars,
            "followers": followers_count,
            "total_public_contributions": calendar_contributions,
            "contrib_data": contributed_to_count,
            "total_commits": total_commits,
            "total_pull_requests": total_prs,
            "total_issues": total_issues,
            "latest_repository": latest_repo,
            "repositories": repos  # List of dicts with name, cloneUrl, default branch data
        }
