import flet as ft
from sqlmodel import SQLModel, Field, create_engine, Session, select, func
from typing import Optional
from datetime import date, datetime
from passlib.context import CryptContext

# ===================== DB =====================
engine = create_engine("sqlite:///database.db")

def create_db():
    SQLModel.metadata.create_all(engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def save_request(client, equipment, fault_type, description,
                status="в ожидании", assigned_to=""):
    """сохранение новой заявки в DB"""
    with Session(engine) as session:
        max_number = session.exec(select(func.max(Request.number))).one()
        next_number = (max_number or 1000) + 1
        
        req = Request(
            number=next_number,
            create_at=date.today(),
            equipment=equipment,
            fault_type=fault_type,
            description=description,
            client=client,
            status=status,
            assigned_to=assigned_to
        )
        
        session.add(req)
        session.commit()
        
        request_number = req.number
        return request_number

# ===================== MODELS =====================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    full_name: Optional[str] = None
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

class Request(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    number: int
    create_at: date
    equipment: str
    fault_type: str
    description: str
    client: str
    status: str
    assigned_to: str

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int
    author: str
    text: str
    created_at: date = Field(default_factory=date.today)

# ===================== APP =====================
def main(page: ft.Page):
    page.title = "Учет заявок на ремонт"
    page.window.width = 1000
    page.window.height = 750
    page.window.resizable = False
    page.window.maximizable = False
    page.bgcolor = "#000000"

    create_db()
    current_user = None

    # ---------- utils ----------
    def show_msg(text, color):
        sb = ft.SnackBar(ft.Text(text, color="WHITE"), bgcolor=color)
        page.overlay.append(sb)
        sb.open = True
        page.update()
        
    def is_admin():
        return current_user and current_user.role == "admin"
    
    # def is_master():
    #     return current_user and current_user.role == "master"
    # ---------- auth ----------
    def register_user(username, password, full_name=""):
        with Session(engine) as db:
            if db.exec(select(User).where(User.username == username)).first():
                raise Exception("Пользователь уже существует")
            db.add(User(
                username=username,
                password_hash=hash_password(password),
                full_name=full_name
            ))
            db.commit()

    def authenticate_user(username, password):
        with Session(engine) as db:
            user = db.exec(select(User).where(User.username == username)).first()
            if not user or not verify_password(password, user.password_hash):
                return None
            if not user.is_active:
                return None
            client_field.value = user.username
            return user

    # ---------- AUTH UI ----------
    login_username = ft.TextField(label="Логин", width=250)
    login_password = ft.TextField(label="Пароль", password=True, width=250)

    reg_username = ft.TextField(label="Логин", width=250)
    reg_password = ft.TextField(label="Пароль", password=True, width=250)
    reg_name = ft.TextField(label="ФИО", width=250)

    def login_handler(e):
        nonlocal current_user
        user = authenticate_user(login_username.value, login_password.value)
        if not user:
            show_msg("Неверный логин или пароль", ft.Colors.RED)
            return
        current_user = user
        show_msg(f"Добро пожаловать, {user.username}", ft.Colors.GREEN)
        show_app()

    def register_handler(e):
        try: 
            if not reg_username.value:
                show_msg("enter username", ft.Colors.RED)
                return

            if not reg_password.value:
                show_msg("enter password", ft.Colors.RED)
                return

            if len(reg_password.value) < 8:
                show_msg("password can't be less 8 symbol", ft.Colors.ORANGE)
                return

            if not reg_name.value:
                show_msg("enter your name", ft.Colors.RED)
                return

            register_user(reg_username.value, reg_password.value, reg_name.value)

            show_msg("Регистрация успешна", ft.Colors.GREEN)
            # Очистка полей
            reg_username.value = ""
            reg_password.value = ""
            reg_name.value = ""
            page.update()
        except Exception as ex:
            show_msg(str(ex), ft.Colors.RED)

    auth_view = ft.Container(
        content=ft.Column(
            [
                ft.Text("Вход", size=22, color="WHITE"),
                login_username,
                login_password,
                ft.Button("Войти", on_click=login_handler, width=250),
                ft.Divider(height=20),
                ft.Text("Регистрация", size=22, color="WHITE"),
                reg_username,
                reg_password,
                reg_name,
                ft.Button("Зарегистрироваться", on_click=register_handler, width=250),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )

    # ---------- ADD REQUEST UI ----------
    equipment_field = ft.TextField(label="Оборудование", width=250, border_color="#0066CC")
    fault_field = ft.TextField(label="Тип неисправности", width=250, border_color="#0066CC")
    client_field = ft.TextField(label="Клиент", width=250, border_color="#0066CC")
    status_field = ft.Dropdown(
        label="Статус",
        width=250,
        options=[
            ft.dropdown.Option("в ожидании"),
            ft.dropdown.Option("в работе"),
            ft.dropdown.Option("выполнено"),
        ],
        value="в ожидании",
        border_color="#0066CC"
    )
    description_field = ft.TextField(
        label="Описание проблемы",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=760,
        border_color="#0066CC"
    )
    assigned_field = ft.TextField(label="Исполнитель", width=250, border_color="#0066CC",)

    def add_request_handler(e):
        if not client_field.value or not equipment_field.value:
            show_msg("Заполните оборудование и клиента", ft.Colors.RED)
            return
        
        try:
            request_number = save_request(
                client=client_field.value,
                equipment=equipment_field.value,
                fault_type=fault_field.value,
                description=description_field.value,
                status=status_field.value,
                assigned_to=assigned_field.value if assigned_field.value else current_user.username
            )
            
            show_msg(f"Заявка #{request_number} создана!", ft.Colors.GREEN)
            
            # Очистка полей
            equipment_field.value = ""
            fault_field.value = ""
            client_field.value = ""
            description_field.value = ""
            assigned_field.value = ""
            status_field.value = "в ожидании"
            
        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", ft.Colors.RED)
        
        page.update()
        
    def load_request(search=""):
        check_status.selected_index = None
        check_status.rows.clear()
        
        # if not is_admin():
        #     show_msg("admin only", ft.Colors.ORANGE)
        #     return
        
        if not search:
            page.update()
            return
        
        with Session(engine) as session:
            stat = select(Request)
            
            if search:
                stat=stat.where(
                    (Request.number.like(f"%{search}%")) |
                    (Request.equipment).like(f"%{search.upper()or search.lower()}%") |
                    (Request.client).like(f"%{search.upper()or search.lower()}%")
                )
            requests = session.exec(stat).all()
            
        for req in requests:
            check_status.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(req.number))),
                        ft.DataCell(ft.Text(str(req.create_at))),
                        ft.DataCell(ft.Text(req.equipment)),
                        ft.DataCell(ft.Text(req.fault_type)),
                        ft.DataCell(ft.Text(req.client)),
                        ft.DataCell(ft.Text(req.status)),
                        ft.DataCell(ft.Text(req.assigned_to)),
                    ]
                )
            )

    page.update()
    
    def status_complete(e):
        """Показывает количество выполненных заявок (только для админа)"""
        if not is_admin():
            show_msg("Только для администратора", ft.Colors.ORANGE)
            return
        
        with Session(engine) as session:
            count = session.exec(
                select(func.count()).where(Request.status == "выполнено")
            ).one()
        
        show_msg(f"Выполнено заявок: {count}", ft.Colors.BLUE)
        return count

    
    add_button = ft.Button(
        "Добавить заявку",
        on_click=add_request_handler,
        width=200
    )

    # ---------- EDIT REQUEST UI ----------
    edit_id_field = ft.TextField(label="ID заявки", width=200, border_color="#0066CC")
    edit_equipment_field = ft.TextField(label="Оборудование", width=250, border_color="#0066CC")
    edit_fault_field = ft.TextField(label="Тип неисправности", width=250, border_color="#0066CC")
    edit_client_field = ft.TextField(label="Клиент", width=250, border_color="#0066CC")
    edit_status_field = ft.Dropdown(
        label="Статус",
        width=250,
        border_color="#0066CC",
        options=[
            ft.dropdown.Option("в ожидании"),
            ft.dropdown.Option("в работе"),
            ft.dropdown.Option("выполнено"),
        ]
    )
    edit_description_field = ft.TextField(
        label="Описание проблемы",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=760,
        border_color="#0066CC"
    )
    edit_assigned_field = ft.TextField(label="Исполнитель", width=250, border_color="#0066CC")

    check_status=ft.DataTable(
        columns=[
            ft.DataColumn(label="№"),
            ft.DataColumn(label="create_at"),
            ft.DataColumn(label="оборудование"),
            ft.DataColumn(label="fail_type"),
            ft.DataColumn(label="client"),
            ft.DataColumn(label="status"),
            ft.DataColumn(label="assigned_to")
            ]
        )

    search_field = ft.TextField(
        label="search (number, client, equipment)",
        on_change=lambda e: load_request(search_field.value)
    )
    

    btn_done_count = ft.Button(
        "Показать выполненные заявки",
        on_click=status_complete,
        width=200
    )
    
    def load_request_for_edit(e):
        if not is_admin():
            show_msg("Only admin function", ft.Colors.ORANGE)
            return                                           #Загрузить данные зая  вки для редактирования
        
        if not edit_id_field.value:
            show_msg("Введите ID заявки", ft.Colors.RED)
            return
        
        try:
            request_id = int(edit_id_field.value)
            with Session(engine) as session:
                request = session.get(Request, request_id)
                if not request:
                    show_msg(f"Заявка с ID {request_id} не найдена", ft.Colors.RED)
                    return
                
                # Заполняем поля данными из БД
                edit_equipment_field.value = request.equipment
                edit_fault_field.value = request.fault_type
                edit_client_field.value = request.client
                edit_description_field.value = request.description
                edit_status_field.value = request.status
                edit_assigned_field.value = request.assigned_to
                
                show_msg(f"Заявка #{request.number} загружена", ft.Colors.GREEN)
                page.update()
                
        except ValueError:
            show_msg("ID должен быть числом", ft.Colors.RED)
        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", ft.Colors.RED)

    def edit_request_handler(e):
        if not is_admin():
            show_msg("Only admin function", ft.Colors.ORANGE)
            return
        
        if not edit_id_field.value:
            show_msg("Введите ID заявки", ft.Colors.RED)
            return
        
        try:
            request_id = int(edit_id_field.value)
            
            with Session(engine) as session:
                request = session.get(Request, request_id)
                if not request:
                    show_msg(f"Заявка с ID {request_id} не найдена", ft.Colors.RED)
                    return
                
                # Обновляем данные
                request.equipment = edit_equipment_field.value
                request.fault_type = edit_fault_field.value
                request.client = edit_client_field.value
                request.description = edit_description_field.value
                request.status = edit_status_field.value
                request.assigned_to = edit_assigned_field.value
                
                session.add(request)
                session.commit()
                
                show_msg(f"Заявка №{request.number} успешно обновлена!", ft.Colors.GREEN)
                
        except ValueError:
            show_msg("ID должен быть числом", ft.Colors.RED)
        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", ft.Colors.RED)

    load_button = ft.Button(
        "Загрузить",
        on_click=load_request_for_edit,
        width=200
    )

    edit_button = ft.Button(
        "Сохранить изменения",
        on_click=edit_request_handler,
        width=200
    )

    # ---------- COMMENT UI ----------
    comment_id_field = ft.TextField(label="ID заявки", width=250, border_color="#0066CC")
    comment_author = ft.TextField(label="Автор", width=250, border_color="#0066CC")
    comment_text = ft.TextField(label="Комментарий", multiline=True, min_lines=3, width=250, border_color="#0066CC")

    def add_comment_handler(e):
        if not comment_id_field.value:
            show_msg("Введите ID заявки", ft.Colors.RED)
            return
        
        if not comment_author.value:
            show_msg("Введите автора", ft.Colors.RED)
            return
        
        if not comment_text.value:
            show_msg("Введите текст комментария", ft.Colors.RED)
            return
        
        try:
            with Session(engine) as session:
                # Проверяем существование заявки
                request = session.get(Request, int(comment_id_field.value))
                if not request:
                    show_msg(f"Заявка с ID {comment_id_field.value} не найдена", ft.Colors.RED)
                    return
                
                comment = Comment(
                    request_id=int(comment_id_field.value),
                    author=comment_author.value,
                    text=comment_text.value
                )
                session.add(comment)
                session.commit()

                show_msg(f"Комментарий #{comment.id} успешно добавлен!", ft.Colors.GREEN)

                # Очищаем поля
                comment_author.value = ""
                comment_text.value = ""
                
                page.update()

        except ValueError:
            show_msg("ID заявки должен быть числом", ft.Colors.RED)
        except Exception as ex:
            show_msg(f"Ошибка: {ex}", ft.Colors.RED)

    comment_button = ft.Button(
        "Добавить комментарий",
        on_click=add_comment_handler,
        width=200
    )

    # ---------- APP VIEW ----------
    app_view = ft.Tabs(
        length=4,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="ДОБАВИТЬ", icon=ft.Icons.ADD),
                        ft.Tab(label="РЕДАКТИРОВАТЬ", icon=ft.Icons.EDIT),
                        ft.Tab(label="КОММЕНТАРИИ", icon=ft.Icons.COMMENT),
                        ft.Tab(label="view", icon=ft.Icons.VIEW_AGENDA)
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        # ВКЛАДКА ДОБАВЛЕНИЯ
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    equipment_field, 
                                    fault_field, 
                                    client_field
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    status_field, 
                                    assigned_field, 
                                    ft.Container(width=250)  # Пустой контейнер для выравнивания
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    description_field
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    add_button
                                ], alignment=ft.MainAxisAlignment.CENTER)
                            ], spacing=20),
                            alignment=ft.Alignment.CENTER,
                            padding=20,
                        ),

                        # ВКЛАДКА РЕДАКТИРОВАНИЯ
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    edit_id_field,
                                    load_button
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    edit_equipment_field, 
                                    edit_fault_field, 
                                    edit_client_field
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    edit_status_field, 
                                    edit_assigned_field,
                                    ft.Container(width=250)
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    edit_description_field
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    edit_button
                                ], alignment=ft.MainAxisAlignment.CENTER)
                            ], spacing=20),
                            alignment=ft.Alignment.CENTER,
                            padding=20,
                        ),

                        # ВКЛАДКА КОММЕНТАРИЕВ
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    comment_id_field
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    comment_author
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    comment_text
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([
                                    comment_button
                                ], alignment=ft.MainAxisAlignment.CENTER)
                            ], spacing=20),
                            alignment=ft.Alignment.CENTER,
                            padding=20,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            search_field,
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER
                                    ),
                                    ft.Divider(),
                                    check_status,
                                    btn_done_count
                                ],
                                expand=True,
                                scroll=ft.ScrollMode.AUTO
                            ),
                            padding=20
                        )
                    ],
                ),
            ],
        ),
    )

    # ---------- LOGOUT BUTTON ----------
    logout_button = ft.IconButton(
        icon=ft.Icons.LOGOUT,
        icon_color="white",
        on_click=lambda e: show_auth(),
        tooltip="Выйти"
    )

    # Добавляем кнопку выхода в app_view
    app_view_with_logout = ft.Column([
        ft.Row([logout_button], alignment=ft.MainAxisAlignment.END),
        app_view
    ], expand=True)

    # ---------- NAV ----------
    def show_auth():
        page.controls.clear()
        page.add(auth_view)
        page.update()

    def show_app():
        page.controls.clear()
        page.add(app_view_with_logout)
        page.update()
        
        if hasattr(app_view, 'tab_bar') and app_view.tab_bar and hasattr(app_view.tab_bar, 'tabs'):
            if len(app_view.tab_bar.tabs) > 1:
                app_view.tab_bar.tabs[1].disabled = not is_admin()

    show_auth()

ft.run(main)