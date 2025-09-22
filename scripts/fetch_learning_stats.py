#!/usr/bin/env python3
"""
Fetch learning stats from daily-learning repository
"""

import os
import re
import json
from datetime import datetime, timedelta
from github import Github
from pathlib import Path

def get_learning_stats(github_token):
    """Fetch stats from daily-learning repository"""
    
    g = Github(github_token)
    
    # Get the daily-learning repository
    repo = g.get_repo('tysoncung/daily-learning')
    
    stats = {
        'learning_days': 0,
        'notes_count': 0,
        'latest_topics': [],
        'pr_mentions': 0,
        'resources_added': 0
    }
    
    try:
        # Check PROGRESS.md for streak info
        progress_file = repo.get_contents('PROGRESS.md')
        progress_content = progress_file.decoded_content.decode('utf-8')
        
        # Extract streak days
        streak_match = re.search(r'Current Streak:\s*(\d+)\s*days?', progress_content)
        if streak_match:
            stats['learning_days'] = int(streak_match.group(1))
        
        # Extract PR count
        pr_match = re.search(r'PRs Opened[:\s]*(\d+)', progress_content)
        if pr_match:
            stats['pr_mentions'] = int(pr_match.group(1))
        
        # Count notes files
        try:
            notes_contents = repo.get_contents('notes')
            stats['notes_count'] = len([f for f in notes_contents if f.name.endswith('.md')])
        except:
            pass
        
        # Get latest learning topics (from most recent note)
        today = datetime.now()
        for days_back in range(7):  # Check last 7 days
            date = today - timedelta(days=days_back)
            note_path = f"notes/{date.strftime('%Y-%m-%d')}.md"
            
            try:
                note_file = repo.get_contents(note_path)
                note_content = note_file.decoded_content.decode('utf-8')
                
                # Extract topics from "What I Learned Today" section
                topics_match = re.search(r'## What I Learned Today\n(.*?)(?:\n##|\Z)', 
                                        note_content, re.DOTALL)
                if topics_match:
                    topics_text = topics_match.group(1)
                    # Extract bullet points
                    topics = re.findall(r'^[-*]\s*\*\*(.*?)\*\*', topics_text, re.MULTILINE)
                    stats['latest_topics'] = topics[:3]  # Get top 3 topics
                    break
            except:
                continue
        
    except Exception as e:
        print(f"Error fetching learning stats: {e}")
    
    return stats

def format_learning_section(stats):
    """Format the learning stats for README"""
    
    section = "## 📚 Daily Learning Journey\n\n"
    
    if stats['learning_days'] > 0:
        section += f"- 📖 **{stats['learning_days']}-day learning streak** active!\n"
    
    if stats['notes_count'] > 0:
        section += f"- 📝 **{stats['notes_count']} learning notes** documented\n"
    
    if stats['latest_topics']:
        section += "- 🎯 **Recent topics**:\n"
        for topic in stats['latest_topics']:
            section += f"  - {topic}\n"
    
    section += f"- 🔗 [View my learning journey](https://github.com/tysoncung/daily-learning)\n"
    
    return section

if __name__ == "__main__":
    # This script can be imported or run standalone
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        stats = get_learning_stats(token)
        print(json.dumps(stats, indent=2))
        print("\n" + format_learning_section(stats))