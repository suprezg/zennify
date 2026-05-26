"""
File Name: test_todos_dashboard.py
Purpose: UI tests for the TodoDashboard using Flet mocking.
"""

import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.todos.dashboard import TodoDashboard

@pytest.fixture
def mock_page():
    """
    Provides a mocked Flet Page object.
    """
    page = MagicMock(spec=ft.Page)
    page.window = MagicMock()
    page.controls = []
    page.add.side_effect = lambda *args: page.controls.extend(args)
    page.overlay = []
    return page

@patch("core.todos.dashboard.TodoTasks")
@patch("core.todos.dashboard.TodoSettings")
@patch("core.todos.dashboard.TodoStatistics")
@patch("core.todos.dashboard.WalletManager")
def test_todo_dashboard_view(mock_wallet, mock_stats, mock_settings, mock_tasks, mock_page):
    """
    Tests if the todo dashboard initializes and renders correctly.
    """
    mock_tasks.return_value.list_running_tasks.return_value = [
        (1, "Test Task", "2026-05-30")
    ]
    mock_tasks.return_value.list_finalized_tasks.return_value = []
    mock_stats.return_value.give_overview.return_value = {"streak": 5, "multiplier": 1.5, "overview_data": []}
    mock_settings.return_value.read_config.return_value = {"max_tasks": 5}
    mock_wallet.return_value.is_bankrupt.return_value = 1
    
    dashboard = TodoDashboard(mock_page)
    dashboard.view()
    
    assert mock_page.title == "Zennify - Hardcore Todos"
    assert len(mock_page.controls) > 0
    assert isinstance(mock_page.controls[0], ft.Tabs)

    tasks_tab = dashboard._tasks_tab()

    second_row = tasks_tab.controls[1]
    running_tasks_container = second_row.controls[0]
    tasks_list = running_tasks_container.content.controls[1]
    
    assert len(tasks_list.controls) == 1
    assert "Test Task" in tasks_list.controls[0].title.value

@patch("core.todos.dashboard.TodoTasks")
@patch("core.todos.dashboard.TodoSettings")
@patch("core.todos.dashboard.TodoStatistics")
@patch("core.todos.dashboard.WalletManager")
def test_todo_dashboard_add_task(mock_wallet, mock_stats, mock_settings, mock_tasks, mock_page):
    """
    Tests adding a task through the dashboard.
    """
    mock_tasks.return_value.list_running_tasks.return_value = []
    mock_tasks.return_value.list_finalized_tasks.return_value = []
    mock_tasks.return_value.add_task.return_value = (True, "Success")
    mock_stats.return_value.give_overview.return_value = {"streak": 0, "multiplier": 1.0, "overview_data": []}
    mock_settings.return_value.read_config.return_value = {"max_tasks": 5}
    
    dashboard = TodoDashboard(mock_page)
    tasks_tab = dashboard._tasks_tab()

    form_row = tasks_tab.controls[0].content
    name_input = form_row.controls[0].controls[1]
    add_btn = form_row.controls[2].controls[1]
    
    name_input.value = "New Task"
    add_btn.on_click(MagicMock())

    mock_tasks.return_value.add_task.assert_called()

@patch("core.todos.dashboard.TodoTasks")
@patch("core.todos.dashboard.TodoSettings")
@patch("core.todos.dashboard.TodoStatistics")
@patch("core.todos.dashboard.WalletManager")
def test_todo_dashboard_complete_task(mock_wallet, mock_stats, mock_settings, mock_tasks, mock_page):
    """
    Tests marking a task as completed.
    """
    mock_tasks.return_value.list_running_tasks.return_value = [(1, "Test Task", "2026-05-30")]
    mock_tasks.return_value.list_finalized_tasks.return_value = []
    mock_stats.return_value.give_overview.return_value = {"streak": 5, "multiplier": 1.5, "overview_data": []}
    mock_settings.return_value.read_config.return_value = {"max_tasks": 5}
    
    dashboard = TodoDashboard(mock_page)
    tasks_tab = dashboard._tasks_tab()

    second_row = tasks_tab.controls[1]
    tasks_list = second_row.controls[0].content.controls[1]
    check_btn = tasks_list.controls[0].trailing
    
    check_btn.on_click(MagicMock())

    mock_tasks.return_value.mark_task.assert_called_with(1, "Completed")
