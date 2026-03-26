import gitlab
import gitlab as gt
import dotenv
import os

import base64

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QApplication, QGroupBox, QComboBox, QCheckBox, QPushButton, QLabel,
                             QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QSpinBox)

dotenv.load_dotenv()
PERSONAL_TOKEN = os.getenv('GITLAB_TOKEN')


class GitLab:
    def __init__(self):
        self.gitlab = gitlab.Gitlab('https://gitlab.com', private_token=PERSONAL_TOKEN)
        self.user = self.gitlab.users.list(username="Mikufg")[0]

        self.projects = {}

        self.get_info()

    def get_info(self):
        print(self.user.username)
        print(self.user.name)

        current_user_id = self.user.id

        projects = self.gitlab.projects.list(membership=True,
                                             owned=False,
                                             all=True)

        for project in projects:
            try:
                detailed_project = self.gitlab.projects.get(project.id)

                member = detailed_project.members.get(current_user_id)
                member_level = member.access_level

                if member_level != 50:
                    branches = []
                    br = detailed_project.branches.list(all=True)
                    for j in br:
                       branches.append(j.name)

                    self.projects[detailed_project.name] = branches
            except Exception as e:
                print(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.gitlab = GitLab()
        self.proj = self.gitlab.projects

        self.setWindowTitle("GitLab")
        self.resize(800, 600)

        c_widget = QWidget(self)
        c_layout = QVBoxLayout(c_widget)

        self.setCentralWidget(c_widget)
        spin_layout = QHBoxLayout()

        rep_layout = QVBoxLayout()
        rep_label = QLabel("Rep")
        rep_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.rep_combo = QComboBox()
        self.rep_combo.setStyleSheet("QComboBox { font-size: 24px; }")
        self.rep_combo.currentTextChanged.connect(self.fill_combo_box_branch)
        self.rep_combo.setMaximumWidth(250)

        rep_layout.addWidget(rep_label)
        rep_layout.addWidget(self.rep_combo)

        spin_layout.addLayout(rep_layout)

        branch_layout = QVBoxLayout()
        branch_label = QLabel("Branch")
        branch_label.setStyleSheet("QLabel { font-size: 24px; }")
        self.branch_combo = QComboBox()
        self.branch_combo.setStyleSheet("QComboBox { font-size: 24px; }")
        self.branch_combo.currentTextChanged.connect(self.setYML)
        self.branch_combo.setMaximumWidth(250)

        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self.branch_combo)

        spin_layout.addLayout(branch_layout)

        c_layout.addLayout(spin_layout)
        c_layout.addSpacing(50)

        self.yml_lb = QLabel("ci: ")
        self.yml_lb.setStyleSheet("QLabel { font-size: 32px;"
                                  "         font-weight: bold; }")
        self.yml_lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(self.yml_lb)

        push = QPushButton("Запустить пайплайн 🦁🦁🦁")
        push.setMaximumWidth(300)
        push.setStyleSheet("QPushButton { font-size: 24px;}")

        push.clicked.connect(self.start_ci)

        c_layout.addWidget(push, alignment=Qt.AlignmentFlag.AlignCenter)

        c_layout.addSpacing(500)

        self.fill_combo_box_rep()

    def fill_combo_box_rep(self):
        for key in self.proj.keys():
            self.rep_combo.addItem(key)

    def fill_combo_box_branch(self):
        self.branch_combo.clear()
        key = self.rep_combo.currentText()
        value = self.proj.get(key)

        for v in value:
            self.branch_combo.addItem(v)

    def setYML(self):
        self.yml_lb.setText(f"{self.rep_combo.currentText()}.{self.branch_combo.currentText()}.gitlab-ci.yml")

    def start_ci(self):
        try:
            # ПРОВЕРЯЕМ: есть ли вообще gitlab клиент
            if not self.gitlab:
                print("❌ self.gitlab не инициализирован!")
                return

            print(f"🔍 Подключение к GitLab: {self.gitlab.url}")

            # ПРОВЕРЯЕМ: пробуем получить информацию о пользователе
            try:
                user = self.gitlab.user
                print(f"✅ Текущий пользователь: {user.username}")
            except Exception as e:
                print(f"❌ Не удалось получить пользователя: {e}")
                return

            # ПРОБУЕМ получить проект
            project_path = 'mikufg-group/testincludeci'
            print(f"🔍 Ищем проект: {project_path}")

            try:
                project = self.gitlab.projects.get(project_path)
                print(f"✅ Проект найден: {project.path_with_namespace}")
                print(f"   ID: {project.id}")
                print(f"   URL: {project.web_url}")
            except Exception as e:
                print(f"❌ Проект не найден: {e}")
                print("   Проверь:")
                print("   - Правильный ли путь к проекту?")
                print("   - Есть ли у тебя доступ к проекту?")
                print("   - Работает ли токен?")
                return
            ci_name = self.yml_lb.text()

            pipeline = project.pipelines.create({
                'ref': 'main',
                'variables': [
                    {'key': 'CI_CONFIG_PATH', 'value': ci_name}  # Путь к файлу
                ]
            })

            print("🚀🚀🚀 CI запущен!!! 🚀🚀🚀")
        except Exception as e:
            print(e)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
