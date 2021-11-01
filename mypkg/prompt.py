from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout, Window, FormattedTextControl
from prompt_toolkit.application.current import get_app
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.dimension import D
from functools import partial

def chunk_selected(text_area, content):
    text_area.text = content

def exit_clicked():
    get_app().exit()
    
def generate_buffer_window(buffer_text, text_area, patch, style):
    window = Window(
        FormattedTextControl(
            text=buffer_text,
            focusable=True,
            key_bindings=generate_buffer_key_bindings(text_area, patch)
        ),
        height=3,
        style=style,
    )

    return window

def generate_chunk_buffers(add_chunks, remove_chunks, text_area):
    buffers = []
    for add_chunk in add_chunks:
        buffer_text = '{} \n({}, {})'.format(add_chunk.context.path, add_chunk.start_id, add_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, add_chunk.generate_add_patch(), "class:add-chunk"))
    for remove_chunk in remove_chunks:
        buffer_text = '{} \n({}, {})'.format(remove_chunk.context.path, remove_chunk.start_id, remove_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, remove_chunk.generate_remove_patch(), "class:remove-chunk"))
        
    return buffers
    
def generate_buffer_key_bindings(text_area, patch):
    kb = KeyBindings()

    @kb.add("c-m")
    def _(event):
        text_area.text = patch

    return kb

def generate_key_bindings():
    kb = KeyBindings()
    kb.add("down")(focus_next)
    kb.add("up")(focus_previous)
    return kb

def generate_chunk_select_prompt(add_chunks, remove_chunks):
    all_chunks = []
    all_chunks.extend(add_chunks)
    all_chunks.extend(remove_chunks)
    text_area = TextArea(focusable=False, read_only=True)
    exit_button = Button("Exit", handler=exit_clicked)
    _chunk_selected = partial(chunk_selected, text_area)
    check_boxes = [Box(body=Label(text="[*]")) for i in range(len(all_chunks))]
    chunk_with_check_boxes = [VSplit([check_boxes[i], generate_chunk_buffers(add_chunks, remove_chunks, text_area)[i]]) for i in range(len(all_chunks))]
    check_box_label = Label(text="Staging State", style="class:chunk-sets")
    chunk_set_label = Label(text="Chunk Sets", style="class:chunk-sets")
    chunk_with_check_boxes.insert(0, VSplit([check_box_label, chunk_set_label]))
    
    root_container = HSplit(
        [
            Label(text="Press `Enter` to show diff, and press 'space' to stage this chunk."),
            VSplit(
                [
                    HSplit(
                        [
                            Label(text="Chunk Sets", style="class:chunk-sets"),
                            HSplit(
                                chunk_with_check_boxes,
                                padding=1,
                            ),
                        ],
                        width=D(max=30, weight=1),
                        style="class:left-pane"
                    ),
                    HSplit(
                        [
                            Label(text="Diff", style="class:diff"),
                            Box(
                                body=Frame(text_area),
                                padding=0,
                                style='class:right-pane',
                            ),
                        ],
                        width=D(weight=3)
                    ),
                ],
                height=D(),
            ),
            exit_button,
        ]
    )

    style = Style(
        [
            ("left-pane", "bg:#454545 #ffffff"),
            ("right-pane", "bg:#000000 #ffffff"),
            ("add-chunk", "bg:#006600 #ffffff"),
            ("remove-chunk", "bg:#880000 #ffffff"),
            ("chunk-sets", "bg:#454545 #ffffff"),
            ("diff", "bg:#000000 #880000"),
            ("buffer focused", "bg:#ffffff"),
        ]
    )
    
    layout = Layout(container=root_container, focused_element=exit_button)
    application = Application(layout=layout, key_bindings=generate_key_bindings(), style=style, full_screen=True, mouse_support=False)
    return application

