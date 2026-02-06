import flet as ft
from sqlmodel import SQLModel, Field, create_engine, Session, select, func
from typing import Optional
from datetime import date, datetime


"""DB"""
engine = create_engine("sqlite:///database.db", echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)
"""DB"""


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
    

"""MODELS"""
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
"""MODELS"""


def main(page: ft.Page):
    page.title = "Учет заявок на ремонт"
    page.window.width = 800
    page.window.height = 700
    page.window.resizable = False
    page.window.maximizable = False
    
    create_db()

    def show_msg(text, bgcolor):
        sb = ft.SnackBar(
            
            content=ft.Text(text, color="WHITE"),
            bgcolor=bgcolor
        )
        page.overlay.append(sb)
        sb.open=True
    
    equipment_field = ft.TextField(label="Оборудование", width=250, border_color=ft.Colors.BLUE)
    fault_field = ft.TextField(label="Тип неисправности", width=250, border_color=ft.Colors.BLUE)
    client_field = ft.TextField(label="Клиент", width=250, border_color=ft.Colors.BLUE)
    status_field = ft.Dropdown(
        label="Статус",
        width=250,
        options=[
            ft.dropdown.Option("в ожидании"),
            ft.dropdown.Option("в работе"),
            ft.dropdown.Option("выполнено"),
        ],
        value="в ожидании",
        border_color=ft.Colors.BLUE
    )
    description_field = ft.TextField(
        label="Описание проблемы",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=760,
        border_color=ft.Colors.BLUE
    )
    assigned_field = ft.TextField(label="Исполнитель", width=250, border_color=ft.Colors.BLUE)

    edit_id_field = ft.TextField(label="ID заявки", width=200, border_color=ft.Colors.BLUE)
    edit_equipment_field = ft.TextField(label="Оборудование", width=250, border_color=ft.Colors.BLUE)
    edit_fault_field = ft.TextField(label="Тип неисправности", width=250, border_color=ft.Colors.BLUE)
    edit_client_field = ft.TextField(label="Клиент", width=250, border_color=ft.Colors.BLUE)
    edit_status_field = ft.Dropdown(
        label="Статус",
        width=250,
        border_color=ft.Colors.BLUE,
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
        border_color=ft.Colors.BLUE
    )
    edit_assigned_field = ft.TextField(label="Исполнитель", width=250, border_color=ft.Colors.BLUE)

    def add_request_handler(e):
        if not client_field.value or not equipment_field.value:
            show_msg("Заполните оборудование и клиента",ft.Colors.RED)
            return
        
        try:
            request_number = save_request(
                client=client_field.value,
                equipment=equipment_field.value,
                fault_type=fault_field.value,
                description=description_field.value,
                status=status_field.value,
                assigned_to=assigned_field.value
            )
            
            show_msg(f"greate! id: {request_number}", ft.Colors.GREEN)
            
            # Очистка полей
            for field in [equipment_field, fault_field, client_field, description_field, assigned_field]:
                field.value = ""
            status_field.value = "в ожидании"
            
        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", ft.Colors.RED)
        
        page.update()

    def edit_request(e):
        """Обработчик для редактирования заявки"""
        if not edit_id_field.value:
            show_msg("Введите ID заявки", ft.Colors.RED)
            return
        
        try:
            request_id = int(edit_id_field.value)
            
            # Сначала найдем заявку, чтобы получить текущие данные
            with Session(engine) as session:
                request = session.get(Request, request_id)
                if not request:
                    show_msg(f"Заявка с ID {request_id} не найдена", ft.Colors.RED)
                    return
            
            # Теперь редактируем
            with Session(engine) as session:
                request = session.get(Request, request_id)
                
                if edit_client_field.value:
                    request.client = edit_client_field.value
                if edit_equipment_field.value:
                    request.equipment = edit_equipment_field.value
                if edit_fault_field.value:
                    request.fault_type = edit_fault_field.value
                if edit_description_field.value:
                    request.description = edit_description_field.value
                if edit_status_field.value:
                    request.status = edit_status_field.value
                if edit_assigned_field.value:
                    request.assigned_to = edit_assigned_field.value
                
                session.add(request)
                session.commit()
                
                show_msg(f"Заявка №{request.number} успешно обновлена!", ft.Colors.GREEN)
                
                # Очищаем поля после редактирования
                edit_id_field.value = ""
                for field in [edit_equipment_field, edit_fault_field, edit_client_field, 
                            edit_description_field, edit_assigned_field]:
                    field.value = ""
                edit_status_field.value = ""
                
        except ValueError:
            show_msg("ID должен быть числом", ft.Colors.RED)
        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", ft.Colors.RED)
        
        page.update()

    add_button = ft.Button(
        "Добавить заявку",
        on_click=add_request_handler,
        width=200
    )

    edit_button = ft.Button(
        "Редактировать заявку",
        on_click=edit_request,
        width=200
    )

    page.add(
    ft.Tabs(
        selected_index=0,
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Tab 1", icon=ft.Icons.ADD),
                        ft.Tab(label="Tab 2", icon=ft.Icons.EDIT),
                        ft.Tab(label="Tab 3", icon=ft.Icons.COMMENT),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([equipment_field, fault_field, client_field]),
                                ft.Row([status_field, assigned_field, ft.Container(width=250)]),
                                description_field,
                                ft.Row([add_button])
                            ]),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([edit_id_field], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Row([edit_equipment_field, edit_fault_field, edit_client_field]),
                                ft.Row([edit_status_field, edit_assigned_field, ft.Container(width=250)]),
                                edit_description_field,
                                ft.Row([edit_button])
                            ]),
                            alignment=ft.Alignment.CENTER,
                            padding=20,
                        ),
                        ft.Container(
                            content=ft.Text("Комментарии"),
                            alignment=ft.Alignment.CENTER,
                        ),
                    ],
                ),
            ],
        ),
    )
    )

    

ft.run(main)