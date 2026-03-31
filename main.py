import os

from together import Together
import flet as ft
from dotenv import load_dotenv
import sqlite3 as sq
from datetime import datetime

# Import an API key:

load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

class HistoryDB:

    def __init__(self):
        self.db_path = "chat_history.db"
        self.create_table()


    def create_table(self):
        with sq.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS history (date TEXT,
                        prompt TEXT,
                        response TEXT
                         )""")
            conn.commit()


    def add_data(self, time, prompt, response):
        with sq.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history VALUES (?, ?, ?)",
                (time, prompt, response),
            )
            conn.commit()

    def query_data(self):
        with sq.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history")
            rows = cursor.fetchall()
        print(rows)
        return rows

    def clear_data(self):
        with sq.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()



def main(page: ft.Page):

    # App configuration:

    page.title = "Flet API Chat"
    page.bgcolor = ft.Colors.GREEN_100
    page.window.width = 740
    page.window.height = 840
    page.scroll = ft.ScrollMode.ALWAYS
    page.window.resizable = False 
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER


    # Initialize DB:


    db = HistoryDB()

    # Function:

    def on_route_change(e):
        page.views.clear()


        if page.route == "/":
            page.views.append(home_view)

        if page.route == "/main_ui":
            page.views.append(main_ui)

        if page.route == "/chat_history":
            page.views.append(chat_history)

        page.update()

    def on_view_pop(e):
        page.views.pop()
        page.update()

    def clear_history(e):

        current_chat = chat_column_main.controls
        current_chat.clear()
        page.update()
        main_ui.update()

    def clear_chat_history(e):
        db.clear_data()
        history_column.controls.clear()
        page.update()
        history_column.update()
        chat_history.update()

    def selected_index_from_route(route: str):
        if route == "/":
            return 0
        elif route == "/main_ui":
            return 1
        elif route == "/chat_history":
            return 2

    def rail():
        return ft.NavigationRail(
            selected_index=selected_index_from_route(page.route),
            label_type=ft.NavigationRailLabelType.ALL,
            extended=True,
            min_extended_width=180,
            expand=True,
            height=150,
            group_alignment=-1.0,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.COMPUTER,
                    selected_icon=ft.Icons.FILTER_1,
                    label="Chat Screen",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SEARCH_ROUNDED,
                    selected_icon=ft.Icons.FILTER_1,
                    label="Chat History",
                ),

            ],
            on_change=lambda e: page.go(
                ["/", "/main_ui", "/chat_history"][e.control.selected_index]
            ),
        )

    async def chat_llm(e):

        print("Loading")

        loading_image = ft.Image("/images/loadState.png", width=200, height=200)
        chat_column_main.controls.append(loading_image)
        page.update()
        

        try:
            if not api_key:
                raise ValueError("Missing TOGETHER_API_KEY in environment or .env")
            if not prompt_entry.value or not prompt_entry.value.strip():
                raise ValueError("Please enter a prompt before sending")
            if not model_dropdown.value:
                raise ValueError("Please select an AI model")

            client = Together(api_key=api_key)

            text_prompt = prompt_entry.value.strip()

            model = model_dropdown.value
            string_now = datetime.now().strftime("%Y-%m-%d %H:%M")

            chat_completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": f"{text_prompt}",
                    }
                ],
            )

            response = chat_completion.choices[0].message.content.replace("**", "").replace("*", "").replace("##", "").replace("       ","").replace("           ","").replace("   ","")

            prompt_response = [text_prompt, response]

            # Add chat time, prompt and response into the Db:

            db.add_data(prompt=text_prompt, response=response, time=string_now)

            # Add the chat card with time, prompt and response:

            response_container = ft.Container(content=ft.Column(controls=[
                ft.Text(
                    value=string_now,
                    size=24,
                ),

                ft.Row(controls=[

                    ft.Image("/images/human.png", width=40, height=40),
                    ft.Container(content=ft.Text(prompt_response[0], color="black", selectable=True), bgcolor=ft.Colors.DEEP_ORANGE_200, padding=10, border_radius=14, width=600)

                ], spacing=7),
                ft.Row(controls=[
                    ft.Image("/images/llm.png", width=40, height=40),
                    ft.Container(content=ft.Text(prompt_response[1], color="black", selectable=True), bgcolor=ft.Colors.WHITE, padding=10, border_radius=14, width=600,)
                ], spacing=7)

            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
            bgcolor=ft.Colors.BLUE_900, 
            padding=24,
            border_radius=14)

            chat_column_main.controls.append(response_container)

            prompt_entry.value = ""
            prompt_entry.update()
            page.update()
            main_ui.update()
            refresh_history_view()


        except Exception as e:
            chat_column_main.controls.append(
                ft.Text(f"Not able to connect: {e}", color=ft.Colors.RED_900)
            )
            page.update()

        finally:
            if loading_image in chat_column_main.controls:
                chat_column_main.controls.remove(loading_image)
            page.update()

    # UI:

    image = ft.Image("/images/fletApi.png", width=200, height=200)
    image2 = ft.Image("/images/softwareLogo.png", width=200, height=200)
    

    image_row = ft.Row(controls=[
        image,
        image2,
    ], alignment=ft.MainAxisAlignment.CENTER)

    model_options = [
        ft.DropdownOption("meta-llama/Llama-3.3-70B-Instruct-Turbo"),
        ft.DropdownOption("deepseek-ai/DeepSeek-R1"),
        ft.DropdownOption("Qwen/Qwen3-235B-A22B-Thinking-2507"),
        ft.DropdownOption("openai/gpt-oss-120b")
    ]

    model_dropdown = ft.Dropdown(label="Select Ai Model", options=model_options, width=300)

    prompt_entry = ft.TextField(label="Enter prompt....",
                                width=400,
                                bgcolor="white",
                                multiline=True,
                                color="black")

    prompt_button = ft.IconButton(icon=ft.Icons.COMPUTER,
                                  width=80,
                                  bgcolor=ft.Colors.BLUE_900,
                                  on_click= chat_llm,
                                  tooltip="Prompt Ai"
                                  )
    
    content_container = ft.Container()
    
    chat_row = ft.Row(controls=[
        prompt_entry,
        prompt_button
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    chat_column = ft.Column(controls=[model_dropdown],  horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    chat_ui = ft.Container(bgcolor=ft.Colors.GREY_600,
                           width=500,
                           height=150,
                           border_radius=10,
                           content=chat_column,

                           padding=48)
    
    chat_ui.scroll = ft.ScrollMode.ALWAYS

    main_column = ft.Column(controls=[
        image_row,
        chat_ui,
        chat_row,
        ft.Button(bgcolor=ft.Colors.BLUE_900, text="Clear Chat View", on_click=clear_history),
        content_container
    ], spacing=24, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # This is where the main chat cards go in the main Ui:

    chat_column_main = ft.Column(spacing=24, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # This is where the history cards get populated:

    history_column= ft.Column(spacing=24, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def refresh_history_view():
        history_column.controls.clear()
        for date, prompt, response in db.query_data():
            history_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(value=date, size=20),
                            ft.Row(
                                controls=[
                                    ft.Image("/images/human.png", width=40, height=40),
                                    ft.Container(
                                        content=ft.Text(prompt, color="black", selectable=True),
                                        bgcolor=ft.Colors.DEEP_ORANGE_200,
                                        padding=10,
                                        border_radius=14,
                                        width=600,
                                    ),
                                ],
                                spacing=7,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Image("/images/llm.png", width=40, height=40),
                                    ft.Container(
                                        content=ft.Text(response, color="black", selectable=True),
                                        bgcolor=ft.Colors.WHITE,
                                        padding=10,
                                        border_radius=14,
                                        width=600,
                                    ),
                                ],
                                spacing=7,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.BLUE_900,
                    padding=24,
                    border_radius=14,
                )
            )


    # Views:

    home_view = ft.View(route="/", controls=[
        rail(),
        ft.Text("Welcome to Flet Api Chat", size=40, color=ft.Colors.PURPLE_900),
        ft.Text("""
Connect with a friendly AI companion powered by the open-source model from the Together API. 
Our chat is designed to be a seamless and intuitive experience, allowing you to have meaningful conversations without worrying about the technicalities. As we explore new ideas and topics together, I'll do my best to provide helpful and accurate information. Feel free to ask me anything - from simple questions to complex problems - and I'll respond with clarity and precision. Whether you're looking for guidance on a project, seeking advice on a personal matter, or simply want to chat about your day, I'm here to listen and assist. So take a deep breath, relax, and let's get started!"""),
        ft.Image("/images/fletApi.png", width=400, height=400),
        ft.Button("Start Chat", bgcolor=ft.Colors.PURPLE_900, on_click=lambda _: page.go("/main_ui"))
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, bgcolor=ft.Colors.BLUE_400, scroll= ft.ScrollMode.ALWAYS)


    main_ui = ft.View(route="/main_ui", controls=[
        rail(),
        main_column,
        chat_column_main
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, bgcolor=ft.Colors.GREEN_100, scroll=ft.ScrollMode.ALWAYS)

    chat_history = ft.View(route="/chat_history", controls=[
        rail(),
        ft.Button("Clear History", icon=ft.Icons.DELETE, on_click=clear_chat_history,
        bgcolor=ft.Colors.ORANGE_400, color="black"),
        history_column,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, bgcolor=ft.Colors.GREEN_100, scroll=ft.ScrollMode.ALWAYS)

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    refresh_history_view()
    page.go(page.route)
    page.update()

if __name__ == "__main__":

    app = ft.app(target=main, assets_dir="assets")

