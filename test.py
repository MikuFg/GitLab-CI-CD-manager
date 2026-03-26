import gitlab
import dotenv
import os
import base64

import time
import random

from gitlab import GitlabGetError

from parse import get_stages, get_jobs_from_stages

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QApplication, QComboBox, QPushButton, QLabel,
                             QHBoxLayout, QVBoxLayout, QWidget, QCheckBox, QLayout, QMessageBox)
from PyQt6.QtGui import QIcon, QPixmap, QMovie

dotenv.load_dotenv()
PERSONAL_TOKEN = os.getenv('GITLAB_TOKEN')
YML_NAME = os.getenv('GITLAB_YML_FILENAME')


class GitLab:
    def __init__(self):
        self.gl = gitlab.Gitlab('https://gitlab.com', private_token=PERSONAL_TOKEN)
        self.user = self.gl.users.list(username="Mikufg")[0] # Получаем текущего пользователя, а не ищем по имени
        self.projects = {}
        self.get_info()

    def get_info(self):
        print(f"Пользователь: {self.user.username}")
        print(f"Имя: {self.user.name}")
        print("-" * 50)

        current_user_id = self.user.id

        # Получаем проекты где пользователь участник, но не владелец
        projects = self.gl.projects.list(
            membership=True,
            owned=False,
            all=True
        )

        print(f"Найдено проектов: {len(projects)}")

        for project in projects:
            try:
                detailed_project = self.gl.projects.get(project.id)

                # Проверяем членство
                member = detailed_project.members.get(current_user_id)
                member_level = member.access_level

                # Если не владелец - получаем ветки
                if member_level != 50:
                    branches = []
                    br = detailed_project.branches.list(all=True)
                    for j in br:
                        branches.append(j.name)

                    # Используем path_with_namespace вместо name для уникальности
                    self.projects[detailed_project.path_with_namespace] = branches
                    print(f"  ✅ {detailed_project.path_with_namespace}: {len(branches)} веток")

            except Exception as e:
                print(f"  ⚠️ Ошибка с проектом {project.path_with_namespace}: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #self.gif = ['dexter_gif.gif', 'ronaldo.gif', 'mega-knight-clash-royale.gif']

        self.count_yellow_card = 0
        self.lines = []

        self.setWindowIcon(QIcon("resources/image/images.jpg"))
        self.gitlab_manager = GitLab()  # Переименовал для ясности
        self.proj = self.gitlab_manager.projects

        self.setWindowTitle("GitLab CIeo Launcher")
        self.resize(800, 600)

        c_widget = QWidget(self)
        c_layout = QVBoxLayout(c_widget)
        self.setCentralWidget(c_widget)

        # Верхняя панель с комбобоксами
        spin_layout = QHBoxLayout()

        # Репозиторий
        rep_layout = QVBoxLayout()
        rep_label = QLabel("Репозиторий")
        rep_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; }")
        self.rep_combo = QComboBox()
        self.rep_combo.setStyleSheet("QComboBox { font-size: 16px; padding: 5px; }")
        self.rep_combo.currentTextChanged.connect(self.fill_combo_box_branch)
        self.rep_combo.setMinimumWidth(300)

        rep_layout.addWidget(rep_label)
        rep_layout.addWidget(self.rep_combo)
        spin_layout.addLayout(rep_layout)

        # Ветка
        branch_layout = QVBoxLayout()
        branch_label = QLabel("Ветка")
        branch_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; }")
        self.branch_combo = QComboBox()
        self.branch_combo.setStyleSheet("QComboBox { font-size: 16px; padding: 5px; }")
        self.branch_combo.currentTextChanged.connect(self.setYML)
        self.branch_combo.currentTextChanged.connect(self.func)
        self.branch_combo.setMinimumWidth(300)

        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self.branch_combo)
        spin_layout.addLayout(branch_layout)

        c_layout.addLayout(spin_layout)
        c_layout.addSpacing(30)

        # Лейбл с именем CI файла
        self.yml_lb = QLabel("Выберите репозиторий и ветку")
        self.yml_lb.setStyleSheet("""
            QLabel { 
                font-size: 20px;
                font-weight: bold;
                color: #2196F3;
                padding: 20px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
        """)
        self.yml_lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.yml_lb.setMinimumHeight(100)
        c_layout.addWidget(self.yml_lb)

        c_layout.addSpacing(30)

        self.check_box_layout = QHBoxLayout()
        c_layout.addLayout(self.check_box_layout)
        c_layout.addSpacing(30)

        # Кнопка запуска
        push = QPushButton("🚀 Запустить пайплайн 🚀")
        push.setMinimumWidth(300)
        push.setMinimumHeight(60)
        push.setStyleSheet("""
            QPushButton { 
                font-size: 20px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        push.clicked.connect(self.start_ci)
        c_layout.addWidget(push, alignment=Qt.AlignmentFlag.AlignCenter)

        c_layout.addStretch()  # Растяжка снизу

        #Доделать
        # elixir_lb = QLabel()
        # elixir_lb.setMinimumWidth(800)
        # movie = QMovie("resources/gifs/Elixir_For_project.gif")
        # elixir_lb.setMovie(movie)
        # movie.setScaledSize(movie.scaledSize().scaled(800, 300, Qt.AspectRatioMode.KeepAspectRatio))
        # movie.start()

        # c_layout.addWidget(elixir_lb)

        # Заполняем комбобоксы
        self.fill_combo_box_rep()

    def func(self): # переименовтаь
        ci_name = YML_NAME
        project_path = 'mikufg-group/testincludeci'

        project = self.gitlab_manager.gl.projects.get(project_path)

        try:
            project.files.get(file_path=ci_name, ref='main')
            file = project.files.get(file_path=ci_name, ref='main')
            content = base64.b64decode(file.content)
            with open("ci/ci.txt", 'wb+') as f:
                f.write(content)

            self.add_check_box()
        except Exception as e:
            print(e)
            self.branch_combo.setCurrentText("main")
            QMessageBox.warning(self, "Warning", f"Error: {e}")

    def add_check_box(self):
        self.clear_layout(self.check_box_layout)
        step = 0

        data = get_stages()
        layout = QVBoxLayout()
        for stage in data:
            if step == 0:
                step += 1
                continue
            check_box = QCheckBox(stage)
            check_box.setObjectName(f"stage_{stage}")
            check_box.stateChanged.connect(self.add_check_box2)

            layout.addWidget(check_box)

        self.check_box_layout.addLayout(layout)

    def add_check_box2(self): # Переименовать (дабвляем лдобы)
        if self.check_box_layout.count() > 1:
            jobs_layout = self.check_box_layout.itemAt(1)
            self.clear_layout(jobs_layout)

            self.check_box_layout.takeAt(1)

        check_boxes = self.findChildren(QCheckBox)
        stages = []

        for check in check_boxes:
            if check.isChecked():
                stages.append(check.text())
            continue

        self.lines, jobs = get_jobs_from_stages(stages)

        layout = QVBoxLayout()
        for job in jobs:
            check_box = QCheckBox(job)
            check_box.setObjectName(f"job_{job}")
            layout.addWidget(check_box)

        self.check_box_layout.addLayout(layout)

    def get_jobs(self):
        stages = []
        jobs = []

        all_check_box = self.findChildren(QCheckBox)

        for cb in all_check_box:
            if cb.objectName().startswith("stage_") and cb.isChecked():
                stages.append(cb.text())
            elif cb.objectName().startswith("job_") and cb.isChecked():
                jobs.append(cb.text())

        if len(stages) == 0 or len(jobs) == 0:
            self.count_yellow_card += 1

            msg = QMessageBox(self)
            msg.setWindowTitle("Предупреждение")
            msg.setText("Убедитесь, что вы выбрали все stages и jobs")
            msg.exec()
            # if self.count_yellow_card <= 1:
            #     msg.setIconPixmap(QPixmap("resources/image/yellow_card.jpg"))
            #     msg.exec()
            # else:
            #     msg.setWindowTitle("Красная карточка")
            #     msg.setIconPixmap(QPixmap("resources/image/red_card.jpg"))
            #     msg.setText("2 недели. Думай над поведением")
            #     msg.exec()
            #     time.sleep(5)
            #     sys.exit()

        return jobs


    # def create_pipline(self):
    #     stages, jobs = self.get_stages_and_jobs()
    #
    #     if not stages or not jobs:
    #         msg = QMessageBox(self)
    #         msg.setWindowTitle("Ошибка")
    #         msg.setText("Не удалось получить stages и jobs")
    #         #msg.setIconPixmap(QPixmap("resources/image/angry_messi.jpg"))
    #         msg.exec()
    #         return []
    #
    #     res = test_pipe(create_pipeline_stages(stages),
    #               create_pipeline_jobs(self.lines, jobs))
    #
    #     if res:
    #         # Создаем QMessageBox
    #         msg = QMessageBox(self)
    #         msg.setWindowTitle("🤩 Успех! 🤩")
    #         msg.setText("Пайплайн успешно записан в файл res_ci.txt")
    #
    #         # Создаем контейнер для GIF
    #         #gif_container = QLabel()
    #         #movie = QMovie(f'resources/gifs/{str(random.choice(self.gif))}')
    #         #gif_container.setMovie(movie)
    #         #movie.start()
    #
    #         # Получаем layout QMessageBox и добавляем GIF
    #         #layout = msg.layout()
    #         # if layout:
    #         #     # Добавляем GIF в верхнюю часть
    #         #     layout.addWidget(gif_container, 0, 0, 1, layout.columnCount())
    #
    #         msg.exec()
    #     else:
    #         msg = QMessageBox(self)
    #         msg.setWindowTitle("Ошибка")
    #         msg.setText("Непредвиденная ошибка")
    #         msg.setIconPixmap(QPixmap("resources/image/angry_messi.jpg"))
    #         msg.exec()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()

    def fill_combo_box_rep(self):
        self.rep_combo.clear()
        for key in self.proj.keys():
            self.rep_combo.addItem(key)

        if self.rep_combo.count() > 0:
            self.rep_combo.setCurrentIndex(0)

    def fill_combo_box_branch(self):
        self.branch_combo.clear()
        key = self.rep_combo.currentText()

        if key and key in self.proj:
            value = self.proj.get(key, [])
            for v in value:
                self.branch_combo.addItem(v)

            if self.branch_combo.count() > 0:
                self.branch_combo.setCurrentIndex(0)

    def setYML(self):
        try:
            repo = self.rep_combo.currentText()
            branch = self.branch_combo.currentText()

            if repo and branch and repo != "" and branch != "":
                # Извлекаем имя проекта из полного пути
                ci_filename = YML_NAME
                self.yml_lb.setText(ci_filename)
            else:
                self.yml_lb.setText("Выберите репозиторий и ветку")
        except Exception as e:
            QMessageBox.warning(self, 'Error', 'Проверьте существует ли данный yml файл.')

    def start_ci(self):
        """Запускает CI пайплайн"""
        try:
            # Проверяем, выбран ли проект
            if not self.rep_combo.currentText():
                print("❌ Выберите репозиторий")
                return

            # Получаем проект
            project_path = 'mikufg-group/testincludeci'
            ci_name = YML_NAME
            print(f"🔍 Ищем проект: {project_path}")

            try:
                project = self.gitlab_manager.gl.projects.get(project_path)
                print(f"✅ Проект найден: {project.path_with_namespace}")
            except Exception as e:
                print(f"❌ Проект не найден: {e}")
                print("Проверь путь к проекту и права доступа")
                return

            print(f"📄 Запускаем CI с файлом: {ci_name}")

            # Проверяем, существует ли файл в репозитории
            try:
                project.files.get(file_path=ci_name, ref='main')
                file = project.files.get(file_path=ci_name, ref='main')
                content = base64.b64decode(file.content)
                print(content)
                with open("ci/ci.txt", 'wb+') as f:
                    f.write(content)
                    print(content)

                with open("ci/ci.txt", 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
                print(f"📁 Файл {ci_name} найден в репозитории")
            except Exception as e:
                print(e)

                return
            # Переменные для пайплайна
            TARGET_BRANCH = self.branch_combo.currentText()
            TARGET_REPO = self.rep_combo.currentText().split('/')[-1]
            print(TARGET_BRANCH, TARGET_REPO)

            # Запускаем пайплайн
            pipeline = project.pipelines.create({
                'ref': 'main',
                'variables': [
                    {'key': 'TARGET_BRANCH', 'value': TARGET_BRANCH},
                    {'key': 'TARGET_REPO', 'value': TARGET_REPO}
                ]
            })

            name = self.yml_lb.text()
            self.yml_lb.setText(f"<a href= {pipeline.web_url}>{name}</a>")
            self.yml_lb.setOpenExternalLinks(True)

            accepted_jobs = self.get_jobs()
            all_jobs = pipeline.jobs.list()

            while True:
                try:
                    pipeline.refresh()  # Обновляем статус самого пайплайна
                except GitlabGetError:
                    print("❌ Не удалось обновить данные пайплайна")
                    break

                # Если весь пайплайн упал, отменен или заблокирован
                if pipeline.status in ['failed', 'canceled', 'skipped']:
                    print(f"❌ Пайплайн завершился со статусом: {pipeline.status}")
                    break

                # Получаем актуальный список "легких" объектов джоб
                # all=True нужен, чтобы подтянулись все джобы, а не только первая страница
                current_jobs_light = pipeline.jobs.list(all=True)

                # Ищем джобу клонирования
                clone_job = next((j for j in current_jobs_light if j.name == 'clone_project'), None)

                if not clone_job:
                    print("⚠️ Джоба 'clone_project' не найдена в пайплайне")
                    break

                # Логика в зависимости от статуса клонирования
                if clone_job.status == 'failed':
                    print("❌ Ошибка в джобе клонирования. Дальнейший запуск невозможен.")
                    break

                if clone_job.status == 'success':
                    print("✅ Клонирование завершено. Проверяем выбранные джобы...")

                    all_started_or_done = True

                    for job_name in accepted_jobs:
                        # Ищем информацию о нужной джобе в списке
                        job_info = next((j for j in current_jobs_light if j.name == job_name), None)

                        if job_info:
                            if job_info.status == 'manual':
                                # КРИТИЧНО: Получаем ПОЛНЫЙ объект через project.jobs.get
                                # чтобы у него был метод .play()
                                try:
                                    full_job = project.jobs.get(job_info.id)
                                    full_job.play()
                                    print(f"▶️ Нажата кнопка Play для: {job_name}")
                                except Exception as e:
                                    print(f"❌ Ошибка при запуске {job_name}: {e}")

                            elif job_info.status in ['created', 'pending']:
                                # Джоба еще не перешла в статус manual (ждет очередь)
                                print(f"⏳ {job_name} еще готовится (статус: {job_info.status})...")
                                all_started_or_done = False

                            elif job_info.status in ['running', 'success']:
                                # Джоба уже в работе или успешно завершена
                                continue

                            elif job_info.status == 'failed':
                                print(f"❌ Джоба {job_name} провалилась!")
                                # Тут решайте сами: выходить из цикла или продолжать другие
                        else:
                            print(f"❓ Джоба {job_name} не найдена в текущем пайплайне")

                    # Если все джобы запущены или уже завершены — выходим из цикла мониторинга
                    if all_started_or_done:
                        print("🎉 Все выбранные задачи успешно запущены!")
                        break
                else:
                    print(f"⏳ Клонирование всё еще в статусе: {clone_job.status}...")

                # Интервал между проверками, чтобы не спамить API GitLab
                time.sleep(5)

            # for job in all_jobs:
            #     if job.name in accepted_jobs:
            #         print(job.name, job.status)
            #         if job.status == 'manual':
            #             job.play()
            #             print(f"✅ Запущена джоба: {job.name}")
            #         else:
            #             print(f"⚠️ Джоба {job.name} имеет статус {job.status}, пропуск.")

            print("\n" + "=" * 50)
            print("🚀🚀🚀 CI ПАЙПЛАЙН ЗАПУЩЕН 🚀🚀🚀")
            print("=" * 50)
            print(f"URL: {pipeline.web_url}")
            print(f"ID: {pipeline.id}")
            print(f"Статус: {pipeline.status}")
            print("=" * 50)

        except Exception as e:
            print(f"❌ Ошибка при запуске CI: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())