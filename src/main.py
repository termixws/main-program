import flet as ft
from sqlmodel import SQLModel, Field, create_engine, Session, select, func
from typing import Optional
from datetime import date

"""DB"""
engine = create_engine("sqlite:///database.db", echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)
"""DB"""

def save_request(client, equipment, fault_type, description, status="в ожидании", assigned_to=""):
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
    password: str
    role: str


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
    created_at: date
"""MODELS"""


def main(page: ft.Page):
    page.title = "Учет заявок на ремонт"
    page.window.width = 800
    page.window.height = 700
    page.window.resizable = False
    page.window.maximizable = False
    
    create_db()
    
    equipment_field = ft.TextField(label="Оборудование", width=250)
    fault_field = ft.TextField(label="Тип неисправности", width=250)
    client_field = ft.TextField(label="Клиент", width=250)
    status_field = ft.Dropdown(
        label="Статус",
        width=250,
        options=[
            ft.dropdown.Option("в ожидании"),
            ft.dropdown.Option("в работе"),
            ft.dropdown.Option("выполнено"),
        ],
        value="в ожидании"
    )
    description_field = ft.TextField(
        label="Описание проблемы",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=760
    )
    assigned_field = ft.TextField(label="Исполнитель", width=250)
    
    def add_request_handler(e):
        if not client_field.value or not equipment_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Заполните оборудование и клиента"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            # Сохраняем заявку и получаем номер
            request_number = save_request(
                client=client_field.value,
                equipment=equipment_field.value,
                fault_type=fault_field.value,
                description=description_field.value,
                status=status_field.value,
                assigned_to=assigned_field.value
            )
            
            # Успешное сообщение (используем сохраненный номер)
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Заявка #{request_number} создана!"), 
                bgcolor=ft.Colors.GREEN
            )
            page.snack_bar.open = True
            
            # Очистка формы
            for field in [equipment_field, fault_field, client_field, description_field, assigned_field]:
                field.value = ""
            status_field.value = "в ожидании"
            
        except Exception as ex:
            # Ошибка
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Ошибка: {str(ex)}"), 
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
        
        page.update()
    
    def clear_form(e):
        equipment_field.value = ""
        fault_field.value = ""
        client_field.value = ""
        description_field.value = ""
        assigned_field.value = ""
        status_field.value = "в ожидании"
        page.update()
    
    add_button = ft.Button(
        "Добавить заявку",
        on_click=add_request_handler,
        width=200
    )
    
    clear_button = ft.Button(
        "Очистить форму",
        on_click=clear_form,
        width=200
    )
    
    page.add(
        ft.Column([
            ft.Text("Создание новой заявки", 
                   size=24, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.BLUE_700),
            
            # Первая строка полей
            ft.Row([equipment_field, fault_field, client_field]),
            
            # Вторая строка полей
            ft.Row([status_field, assigned_field, ft.Container(width=250)]),
            
            # Большое поле описания
            description_field,
            
            # Кнопки
            ft.Row([add_button, clear_button], 
                  alignment=ft.MainAxisAlignment.CENTER, 
                  spacing=20),
            
            # Информационный текст
            ft.Container(
                content=ft.Column([
                    ft.Divider(height=20),
                    ft.Text("Примечания:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("• Номер заявки генерируется автоматически", size=12),
                    ft.Text("• Обязательные поля: Оборудование и Клиент", size=12),
                    ft.Text("• Дата добавления устанавливается автоматически", size=12),
                ], spacing=5),
                padding=10,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                width=760
            )
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
    )


ft.run(main)