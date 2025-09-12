#!/usr/bin/env python3
"""
Update GitHub Profile README with dynamic content and fresh statistics
"""

import json
import re
import os
from datetime import datetime
import requests
from typing import Dict, List, Optional

class GitHubProfileUpdater:
    def __init__(self, username: str = "tysoncung"):
        self.username = username
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
    
    def get_user_stats(self) -> Dict:
        """Fetch user statistics from GitHub API"""
        try:
            url = f"https://api.github.com/users/{self.username}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching user stats: {e}")
        return {}
    
    def get_repo_stats(self) -> List[Dict]:
        """Fetch repository statistics"""
        repos = []
        try:
            url = f"https://api.github.com/users/{self.username}/repos"
            params = {'sort': 'updated', 'per_page': 100}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                repos = response.json()
        except Exception as e:
            print(f"Error fetching repos: {e}")
        return repos
    
    def calculate_metrics(self, repos: List[Dict]) -> Dict:
        """Calculate various metrics from repositories"""
        metrics = {
            'total_stars': 0,
            'total_forks': 0,
            'languages': {},
            'recent_repos': [],
            'popular_repos': []
        }
        
        for repo in repos:
            if not repo.get('fork'):  # Skip forked repos
                metrics['total_stars'] += repo.get('stargazers_count', 0)
                metrics['total_forks'] += repo.get('forks_count', 0)
                
                # Track languages
                if repo.get('language'):
                    lang = repo['language']
                    metrics['languages'][lang] = metrics['languages'].get(lang, 0) + 1
        
        # Get recent repos (last 5 updated)
        metrics['recent_repos'] = sorted(
            [r for r in repos if not r.get('fork')],
            key=lambda x: x.get('updated_at', ''),
            reverse=True
        )[:5]
        
        # Get popular repos (top 5 by stars)
        metrics['popular_repos'] = sorted(
            [r for r in repos if not r.get('fork')],
            key=lambda x: x.get('stargazers_count', 0),
            reverse=True
        )[:5]
        
        return metrics
    
    def update_readme(self, readme_path: str = 'README.md'):
        """Update README with fresh data"""
        # Read current README
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Get fresh data
        user_stats = self.get_user_stats()
        repos = self.get_repo_stats()
        metrics = self.calculate_metrics(repos)
        
        # Add timestamp for cache busting
        timestamp = int(datetime.now().timestamp())
        
        # Update all stats image URLs with cache parameter
        stat_urls = [
            'github-readme-stats.vercel.app/api',
            'github-readme-stats.vercel.app/api/top-langs',
            'github-readme-streak-stats.herokuapp.com',
            'github-profile-summary-cards.vercel.app',
            'github-profile-trophy.vercel.app'
        ]
        
        for url in stat_urls:
            pattern = f'({re.escape(url)}[^"]*)'
            content = re.sub(
                pattern,
                lambda m: self._add_cache_param(m.group(1), timestamp),
                content
            )
        
        # Update dynamic stats section if exists
        if '<!-- STATS:START -->' in content and '<!-- STATS:END -->' in content:
            stats_content = f"""<!-- STATS:START -->
<div align="center">
  <img src="https://img.shields.io/badge/Total%20Repos-{user_stats.get('public_repos', 0)}-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Total%20Stars-{metrics['total_stars']}-yellow?style=flat-square" />
  <img src="https://img.shields.io/badge/Total%20Forks-{metrics['total_forks']}-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Followers-{user_stats.get('followers', 0)}-red?style=flat-square" />
</div>
<!-- STATS:END -->"""
            
            content = re.sub(
                r'<!-- STATS:START -->.*?<!-- STATS:END -->',
                stats_content,
                content,
                flags=re.DOTALL
            )
        
        # Update last updated timestamp
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        if '<!-- Last updated:' in content:
            content = re.sub(
                r'<!-- Last updated:.*?-->',
                f'<!-- Last updated: {update_time} -->',
                content
            )
        else:
            content = content.rstrip() + f'\n\n<!-- Last updated: {update_time} -->\n'
        
        # Update recent activity if section exists
        if '<!-- RECENT:START -->' in content and '<!-- RECENT:END -->' in content:
            recent_content = '<!-- RECENT:START -->\n'
            for repo in metrics['recent_repos'][:3]:
                recent_content += f"- 🔨 Updated [{repo['name']}]({repo['html_url']})\n"
            recent_content += '<!-- RECENT:END -->'
            
            content = re.sub(
                r'<!-- RECENT:START -->.*?<!-- RECENT:END -->',
                recent_content,
                content,
                flags=re.DOTALL
            )
        
        # Write updated content
        with open(readme_path, 'w') as f:
            f.write(content)
        
        print(f"✅ README updated successfully at {update_time}")
        print(f"📊 Stats: {user_stats.get('public_repos', 0)} repos, {metrics['total_stars']} stars, {user_stats.get('followers', 0)} followers")
    
    def _add_cache_param(self, url: str, timestamp: int) -> str:
        """Add or update cache parameter in URL"""
        # Remove existing cache parameter if present
        url = re.sub(r'[&?]cache=\d+', '', url)
        
        # Add new cache parameter
        separator = '&' if '?' in url else '?'
        return f"{url}{separator}cache={timestamp}"


def main():
    """Main function"""
    updater = GitHubProfileUpdater()
    updater.update_readme()


if __name__ == "__main__":
    main()