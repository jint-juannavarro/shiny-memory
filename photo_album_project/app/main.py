import re
import glob
import math
import random
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import Client, app, ui

# modify module path to other .py file to safely store secrets
import user_secrets

# Define unrestricted page routes
unrestricted_page_routes = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get("authenticated", False):
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in unrestricted_page_routes
            ):
                app.storage.user["referrer_path"] = (
                    request.url.path
                )  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


# Restricts access to all pages until authenticated
app.add_middleware(AuthMiddleware)


# Styling and dimensions
int_images_per_page = 60
int_columns = 3
tailwind = "mb-2 p-2 h-[480px] bg-blue-100 break-inside-avoid"
img_card_style = f"columns-{int_columns} w-full gap-2"

# Get wedding photos from computer
wedding_image_list = glob.glob("images/all_photos_compress/*.jpg")
wedding_image_list.sort()
wedding_image_list_full_size = glob.glob("images/all_photos_compress/*.jpg")
wedding_image_list_full_size.sort()
number_of_image_splits = math.ceil(len(wedding_image_list) / int_images_per_page)

# Add photos and zip files to app server
app.add_static_files("/all_photos", "images/all_photos")
app.add_static_files("/all_photos_compress", "images/all_photos_compress")


# Sort img_list based on personal perference
def user_sort_list(img_list: list):
    # Lists to hold numbers based on their remainders when divided by 3
    remainder_0 = [x for x in img_list if int(x[-8:-4]) % 3 == 0]
    remainder_1 = [x for x in img_list if int(x[-8:-4]) % 3 == 1]
    remainder_2 = [x for x in img_list if int(x[-8:-4]) % 3 == 2]

    # Concatenate the lists in the desired order
    rearranged_list = remainder_0 + remainder_1 + remainder_2
    return rearranged_list


# Create appropiate nav buttons based on page
def create_navigation_buttons(str_page: str):
    int_page = int(str_page)
    with ui.row():
        if int_page > 0:
            ui.button(
                icon="arrow_back",
                on_click=lambda int_page=int_page: ui.navigate.to(
                    f"/image/image_group_{int_page-1}"
                ),
            )
        else:
            ui.button(icon="home", on_click=lambda: ui.navigate.to("/home"))

        if int_page < number_of_image_splits - 1:
            ui.button(
                icon="arrow_forward",
                on_click=lambda int_page=int_page: ui.navigate.to(
                    f"/image/image_group_{int_page+1}"
                ),
            )
        else:
            ui.button(icon="home", on_click=lambda: ui.navigate.to("/home"))


# Used to get image id from filename
def find_first_four_digit_sequence(input_string):
    pattern = r"\d{4}"  # Regex pattern to match 4 consecutive digits
    match = re.search(pattern, input_string)
    if match:
        return match.group(0)  # Return the matched string
    else:
        return "0000"  # Return "0000" if no match found


@ui.page("/")
def main_page() -> None:
    with ui.column().classes("absolute-center items-center"):
        ui.label(f'Hello {app.storage.user["username"]}!').classes("text-2xl")
        ui.link("View Photos", "/home").classes("text-2xl")
        ui.label("Log Out").classes("text-2xl")
        ui.button(
            on_click=lambda: (app.storage.user.clear(), ui.navigate.to("/login")),
            icon="logout",
        ).props("outline round")


@ui.page("/login")
def login() -> Optional[RedirectResponse]:
    def try_login() -> (
        None
    ):  # local function to avoid passing username and password as arguments
        if user_secrets.PASSWORDS.get(username.value) == password.value:
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.navigate.to(
                app.storage.user.get("referrer_path", "/")
            )  # go back to where the user wanted to go
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button("Log in", on_click=try_login)
    return None


# Page to download all images
@ui.page("/download-all")
def download_all():
    wedding_image_list = glob.glob("images/all_photos/*.jpg")
    wedding_image_list.sort()
    int_random_image = random.randint(0, len(wedding_image_list))
    ui.button(icon="home", on_click=lambda: ui.navigate.to("/home"))
    ui.button(
        "Download All Photos",
        icon="download",
        on_click=lambda: ui.download(
            "/all_photos/photos.zip", media_type="application/zip"
        ),
    )
    ui.image(wedding_image_list[int_random_image]).classes("w-1/3 h-1/3")


# View segment of images (for speed and stability purposes
@ui.page("/image/image_group_{page}")
def image_group_page(page):
    lower_split = int(int(page) * int_images_per_page)
    upper_split = int((int(page) + 1) * int_images_per_page)
    img_list_to_display = wedding_image_list[lower_split:upper_split]
    img_list_to_display = user_sort_list(img_list_to_display)
    create_navigation_buttons(page)
    with ui.element("div").classes(img_card_style):
        for _, image in enumerate(img_list_to_display):
            with ui.card().classes(tailwind):
                img_id = find_first_four_digit_sequence(image)
                ui.label(f"ID: {img_id}").classes("gap-0")
                ui.image(image).classes("w-full h-full gap-0")
                ui.button(
                    icon="download",
                    on_click=lambda id=img_id: ui.download(
                        f"/all_photos/photo_{id}.jpg",
                        media_type="image/jpeg",
                    ),
                ).classes("gap-0")
    create_navigation_buttons(page)


@ui.page("/home")
def home():
    ui.label("Photo Album").classes("text-5xl font-bold")
    ui.link("Download All Photos", download_all)
    ui.label("View Photos").classes("text-2xl")
    with ui.row():
        for page in range(number_of_image_splits):
            ui.button(
                f"{page}",
                on_click=lambda page=page: ui.navigate.to(f"/image/image_group_{page}"),
            )


ui.run(port=9000, title="Photo Album", favicon="", storage_secret=user_secrets.STORAGE_SECRET)
