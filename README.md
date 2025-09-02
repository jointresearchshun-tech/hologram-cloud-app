project-root/
├─ app.py
├─ requirements.txt
├─ config/
│   ├─ __init__.py
│   ├─ settings.py
│   └─ logging_config.py
├─ services/
│   ├─ __init__.py
│   ├─ github_storage.py
│   ├─ colab_client.py
│   └─ utils.py
├─ ui/
│   ├─ __init__.py
│   ├─ sidebar.py
│   ├─ github_ui.py
│   ├─ colab_ui.py           # manual server input
│   ├─ file_ui.py
│   ├─ processing_ui.py
│   └─ job_ui.py
├─ state/
│   ├─ __init__.py
│   └─ session_manager.py
└─ practical_colab_solution/
    └─ integrated_colab_ui.py  # secrets-based auto connect
