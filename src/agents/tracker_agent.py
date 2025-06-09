# tracker_agent.py
import os
import streamlit as st
from datetime import datetime, timedelta
import google.generativeai as genai
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class TrackerAgent:
    def __init__(self):
        """Initialize the Progress Tracker Agent."""
        # Initialize session state for tracking data
        if 'study_progress' not in st.session_state:
            st.session_state.study_progress = {
                'daily_tasks': {},  # Format: {date: {task_id: completion_status}}
                'study_streaks': [],
                'weekly_summaries': [],
                'achievements': []
            }
        
        if 'task_completions' not in st.session_state:
            st.session_state.task_completions = {}
    
    def parse_study_plan_tasks(self, study_plan: str, plan_duration: str) -> dict:
        """Extract daily tasks from study plan text."""
        tasks_by_day = {}
        
        # Simple parsing logic - look for day patterns
        lines = study_plan.split('\n')
        current_day = None
        current_tasks = []
        
        for line in lines:
            line = line.strip()
            
            # Look for day patterns (Day 1, Day 2, etc.)
            if 'Day' in line and any(char.isdigit() for char in line):
                if current_day and current_tasks:
                    tasks_by_day[current_day] = current_tasks
                
                current_day = line
                current_tasks = []
            
            # Look for task-like patterns (bullets, dashes, numbers)
            elif line and current_day and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                # Extract task description and estimated time
                task_text = line.lstrip('-•*').strip()
                if task_text:
                    current_tasks.append({
                        'id': f"{current_day}_{len(current_tasks) + 1}",
                        'description': task_text,
                        'completed': False,
                        'date_completed': None
                    })
        
        # Add the last day's tasks
        if current_day and current_tasks:
            tasks_by_day[current_day] = current_tasks
        
        return tasks_by_day
    
    def display_daily_tasks(self, tasks_by_day: dict):
        """Display daily tasks with checkboxes for completion tracking."""
        if not tasks_by_day:
            st.info("No study plan tasks found. Please create a study plan in the Study Planner tab first.")
            return
        
        st.markdown("### 📋 Daily Task Tracker")
        
        # Get today's date for highlighting current day
        today = datetime.now().date()
        
        # Display tasks by day
        for day_name, tasks in tasks_by_day.items():
            with st.expander(f"📅 {day_name}", expanded=True):
                day_completion = []
                
                for task in tasks:
                    task_id = task['id']
                    
                    # Check if task is already completed
                    is_completed = st.session_state.task_completions.get(task_id, False)
                    
                    # Display checkbox for task completion
                    completed = st.checkbox(
                        task['description'],
                        value=is_completed,
                        key=f"task_{task_id}"
                    )
                    
                    # Update completion status
                    if completed != is_completed:
                        st.session_state.task_completions[task_id] = completed
                        if completed:
                            # Mark completion date
                            task['date_completed'] = datetime.now().isoformat()
                        else:
                            task['date_completed'] = None
                    
                    day_completion.append(completed)
                
                # Show daily progress
                if day_completion:
                    completed_count = sum(day_completion)
                    total_count = len(day_completion)
                    progress_percentage = (completed_count / total_count) * 100
                    
                    st.progress(progress_percentage / 100)
                    st.write(f"**Progress: {completed_count}/{total_count} tasks ({progress_percentage:.1f}%)**")
    
    def calculate_overall_progress(self, tasks_by_day: dict) -> dict:
        """Calculate overall progress statistics."""
        total_tasks = 0
        completed_tasks = 0
        
        for day_name, tasks in tasks_by_day.items():
            for task in tasks:
                total_tasks += 1
                if st.session_state.task_completions.get(task['id'], False):
                    completed_tasks += 1
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percentage': progress_percentage,
            'remaining_tasks': total_tasks - completed_tasks
        }
    
    def display_progress_overview(self, progress_stats: dict):
        """Display overall progress overview with visualizations."""
        st.markdown("### 📊 Progress Overview")
        
        # Progress metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Tasks",
                value=progress_stats['total_tasks']
            )
        
        with col2:
            st.metric(
                label="Completed",
                value=progress_stats['completed_tasks']
            )
        
        with col3:
            st.metric(
                label="Remaining",
                value=progress_stats['remaining_tasks']
            )
        
        with col4:
            st.metric(
                label="Progress",
                value=f"{progress_stats['progress_percentage']:.1f}%"
            )
        
        # Main progress bar
        st.markdown("#### 🎯 Overall Study Plan Progress")
        progress_bar_col1, progress_bar_col2 = st.columns([3, 1])
        
        with progress_bar_col1:
            st.progress(progress_stats['progress_percentage'] / 100)
        
        with progress_bar_col2:
            st.markdown(f"**{progress_stats['progress_percentage']:.1f}%**")
    
    def get_quiz_performance_data(self) -> list:
        """Get quiz performance data from session state."""
        return st.session_state.get('quiz_history', [])
    
    def display_quiz_performance_chart(self, quiz_data: list):
        """Display quiz performance trends."""
        if not quiz_data:
            st.info("No quiz data available. Take some quizzes to see performance trends!")
            return
        
        st.markdown("### 📈 Quiz Performance Trends")
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(quiz_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create line chart for quiz scores over time
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['score_percentage'],
            mode='lines+markers',
            name='Quiz Scores',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Quiz Performance Over Time",
            xaxis_title="Date",
            yaxis_title="Score Percentage (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance summary
        if len(quiz_data) > 1:
            avg_score = sum(q['score_percentage'] for q in quiz_data) / len(quiz_data)
            latest_score = quiz_data[-1]['score_percentage']
            best_score = max(q['score_percentage'] for q in quiz_data)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col2:
                st.metric("Latest Score", f"{latest_score:.1f}%")
            with col3:
                st.metric("Best Score", f"{best_score:.1f}%")
    
    def calculate_study_streak(self, tasks_by_day: dict) -> int:
        """Calculate current study streak based on daily task completions."""
        # Get completion dates
        completion_dates = []
        
        for day_name, tasks in tasks_by_day.items():
            day_completed = False
            for task in tasks:
                if st.session_state.task_completions.get(task['id'], False):
                    day_completed = True
                    break
            
            if day_completed:
                # For simplicity, use current date - in real app, you'd track actual completion dates
                completion_dates.append(datetime.now().date())
        
        # Calculate streak (simplified version)
        if not completion_dates:
            return 0
        
        # For demo purposes, return a simple count
        return len(set(completion_dates))
    
    def display_achievements(self, progress_stats: dict, quiz_data: list, study_streak: int):
        """Display achievements and badges."""
        st.markdown("### 🏆 Achievements")
        
        achievements = []
        
        # Task completion achievements
        if progress_stats['progress_percentage'] >= 100:
            achievements.append({"name": "Plan Completed", "icon": "🎯", "description": "Completed entire study plan"})
        elif progress_stats['progress_percentage'] >= 75:
            achievements.append({"name": "Almost There", "icon": "🚀", "description": "Completed 75% of study plan"})
        elif progress_stats['progress_percentage'] >= 50:
            achievements.append({"name": "Halfway Hero", "icon": "⭐", "description": "Completed 50% of study plan"})
        elif progress_stats['progress_percentage'] >= 25:
            achievements.append({"name": "Getting Started", "icon": "🌟", "description": "Completed 25% of study plan"})
        
        # Quiz achievements
        if quiz_data:
            avg_score = sum(q['score_percentage'] for q in quiz_data) / len(quiz_data)
            if avg_score >= 90:
                achievements.append({"name": "Quiz Master", "icon": "🧠", "description": "Average quiz score above 90%"})
            elif avg_score >= 80:
                achievements.append({"name": "Smart Learner", "icon": "🎓", "description": "Average quiz score above 80%"})
            
            if len(quiz_data) >= 10:
                achievements.append({"name": "Quiz Enthusiast", "icon": "📚", "description": "Completed 10+ quizzes"})
            elif len(quiz_data) >= 5:
                achievements.append({"name": "Quiz Explorer", "icon": "🔍", "description": "Completed 5+ quizzes"})
        
        # Study streak achievements
        if study_streak >= 30:
            achievements.append({"name": "Consistent Learner", "icon": "🔥", "description": "30+ day study streak"})
        elif study_streak >= 7:
            achievements.append({"name": "Week Warrior", "icon": "💪", "description": "7+ day study streak"})
        
        # Display achievements
        if achievements:
            cols = st.columns(min(len(achievements), 3))
            for i, achievement in enumerate(achievements):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;">
                        <div style="font-size: 2rem;">{achievement['icon']}</div>
                        <div style="font-weight: bold; margin: 0.5rem 0;">{achievement['name']}</div>
                        <div style="font-size: 0.8rem; color: #666;">{achievement['description']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Complete tasks and take quizzes to earn achievements! 🏆")
    
    def display_weekly_summary(self, progress_stats: dict, quiz_data: list):
        """Display weekly progress summary."""
        st.markdown("### 📅 Weekly Summary")
        
        # Get recent quiz data (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_quizzes = [
            q for q in quiz_data 
            if datetime.strptime(q['date'], "%Y-%m-%d %H:%M:%S") > week_ago
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 Task Progress")
            st.write(f"• Tasks completed: {progress_stats['completed_tasks']}")
            st.write(f"• Overall progress: {progress_stats['progress_percentage']:.1f}%")
            st.write(f"• Tasks remaining: {progress_stats['remaining_tasks']}")
        
        with col2:
            st.markdown("#### 🎯 Quiz Activity")
            if recent_quizzes:
                avg_recent_score = sum(q['score_percentage'] for q in recent_quizzes) / len(recent_quizzes)
                st.write(f"• Quizzes taken: {len(recent_quizzes)}")
                st.write(f"• Average score: {avg_recent_score:.1f}%")
                st.write(f"• Best score: {max(q['score_percentage'] for q in recent_quizzes):.1f}%")
            else:
                st.write("• No quizzes taken this week")
                st.write("• Take a quiz to track performance!")
    
    def generate_progress_report(self, progress_stats: dict, quiz_data: list, study_streak: int) -> str:
        """Generate a comprehensive progress report for download."""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        report = f"""
### 📊 EduMate Progress Report
**Generated:** {current_date}

---

#### 📋 Study Plan Progress
• Total Tasks: {progress_stats['total_tasks']}
• Completed Tasks: {progress_stats['completed_tasks']}
• Progress Percentage: {progress_stats['progress_percentage']:.1f}%
• Remaining Tasks: {progress_stats['remaining_tasks']}

#### 🎯 Quiz Performance Summary
"""
        
        if quiz_data:
            avg_score = sum(q['score_percentage'] for q in quiz_data) / len(quiz_data)
            best_score = max(q['score_percentage'] for q in quiz_data)
            total_quizzes = len(quiz_data)
            
            report += f"""
• Total Quizzes Taken: {total_quizzes}
• Average Score: {avg_score:.1f}%
• Best Score: {best_score:.1f}%
• Latest Score: {quiz_data[-1]['score_percentage']:.1f}%

#### 📈 Recent Quiz History:
"""
            for quiz in quiz_data[-5:]:  # Last 5 quizzes
                report += f"• {quiz['topic']}: {quiz['score_percentage']:.1f}% ({quiz['grade']}) - {quiz['date']}\n"
        else:
            report += "• No quiz data available yet\n"
        
        report += f"""

#### 🔥 Study Streak
• Current Streak: {study_streak} days

---

*Keep up the great work! Consistency is key to learning success.*

Generated by EduMate AI Assistant
        """
        
        return report.strip()
    
    def display_tracker_interface(self):
        """Main interface for the progress tracker."""
        st.markdown("### 🎯 Study Progress Tracker")
        st.markdown("Track your learning journey, monitor progress, and celebrate achievements!")
        
        # Check if there's an active study plan
        if 'current_study_plan' in st.session_state and st.session_state.current_study_plan:
            # Parse tasks from study plan
            tasks_by_day = self.parse_study_plan_tasks(
                st.session_state.current_study_plan, 
                st.session_state.get('plan_duration', '1 Month')
            )
            
            # Calculate progress
            progress_stats = self.calculate_overall_progress(tasks_by_day)
            
            # Get quiz data
            quiz_data = self.get_quiz_performance_data()
            
            # Calculate study streak
            study_streak = self.calculate_study_streak(tasks_by_day)
            
            # Display main components
            self.display_progress_overview(progress_stats)
            
            st.markdown("---")
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Daily Tasks", "📈 Quiz Performance", "🏆 Achievements", "📊 Summary"])
            
            with tab1:
                self.display_daily_tasks(tasks_by_day)
            
            with tab2:
                self.display_quiz_performance_chart(quiz_data)
            
            with tab3:
                self.display_achievements(progress_stats, quiz_data, study_streak)
            
            with tab4:
                self.display_weekly_summary(progress_stats, quiz_data)
                
                # Download progress report
                if st.button("📄 Generate Progress Report"):
                    report = self.generate_progress_report(progress_stats, quiz_data, study_streak)
                    st.download_button(
                        label="💾 Download Progress Report",
                        data=report,
                        file_name=f"progress_report_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
        
        else:
            # No active study plan
            st.info("📅 No active study plan found. Create a study plan in the Study Planner tab to start tracking your progress!")
            
            # Still show quiz performance if available
            quiz_data = self.get_quiz_performance_data()
            if quiz_data:
                st.markdown("---")
                self.display_quiz_performance_chart(quiz_data)